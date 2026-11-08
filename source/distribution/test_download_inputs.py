"""Authenticate a complete release ZIP before copying only pinned builder inputs."""
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import warnings
import zipfile


def pin(raw):
    return dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


class DownloadInputsTests(unittest.TestCase):
    def api(self):
        try:
            import download_inputs
        except ImportError:
            self.fail('The single release ZIP needs authenticated member retrieval')
        return download_inputs

    def fixture(self, root, *, content=b'owned build differences', name='base-1.1-EN.xdelta',
                duplicate=False, unsafe=False, symlink=False):
        member='Sacred Gold Plus 1.3.2/Developer-Inputs/'+name
        path=root/'release.zip'
        with zipfile.ZipFile(path,'w') as archive:
            info=zipfile.ZipInfo(member)
            if symlink:
                info.create_system=3;info.external_attr=0o120777 << 16
            archive.writestr(info,content)
            if duplicate:
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore',UserWarning)
                    archive.writestr(member,content)
            if unsafe:
                archive.writestr('../outside',b'bad')
        delivery=dict(schema=1,url='https://example.invalid/release.zip',**pin(path.read_bytes()),
                      files=[dict(name=name,member=member,**pin(b'owned build differences'))])
        dest=root/'destination';dest.mkdir(mode=0o700)
        return path,dest,delivery

    def test_local_archive_copies_only_authenticated_member_and_reuses_exact_output(self):
        api=self.api()
        with tempfile.TemporaryDirectory() as td:
            path,dest,delivery=self.fixture(Path(td))
            rows=api.extract_inputs(path,dest,delivery)
            self.assertEqual((dest/'base-1.1-EN.xdelta').read_bytes(),b'owned build differences')
            self.assertEqual([row['status'] for row in rows],['extracted'])
            self.assertEqual([row['status'] for row in api.extract_inputs(path,dest,delivery)],['present'])
            self.assertEqual(sorted(p.name for p in dest.iterdir()),['base-1.1-EN.xdelta'])

    def test_wrong_container_hash_or_member_content_never_publishes_output(self):
        api=self.api()
        for change in ('container','member'):
            with self.subTest(change=change),tempfile.TemporaryDirectory() as td:
                path,dest,delivery=self.fixture(Path(td),content=(b'wrong' if change=='member' else b'owned build differences'))
                if change=='container':delivery['sha256']='0'*64
                with self.assertRaises(ValueError):api.extract_inputs(path,dest,delivery)
                self.assertEqual(list(dest.iterdir()),[])

    def test_duplicate_traversal_and_symlink_members_are_rejected(self):
        api=self.api()
        for change in ('duplicate','unsafe','symlink'):
            with self.subTest(change=change),tempfile.TemporaryDirectory() as td:
                path,dest,delivery=self.fixture(Path(td),**{change:True})
                with self.assertRaises(ValueError):api.extract_inputs(path,dest,delivery)
                self.assertEqual(list(dest.iterdir()),[])

    def test_existing_output_link_or_different_file_is_preserved(self):
        api=self.api()
        for link in (True,False):
            with self.subTest(link=link),tempfile.TemporaryDirectory() as td:
                root=Path(td);path,dest,delivery=self.fixture(root)
                other=root/'original';other.write_bytes(b'keep')
                out=dest/'base-1.1-EN.xdelta'
                if link:out.symlink_to(other)
                else:out.write_bytes(b'keep')
                with self.assertRaises(ValueError):api.extract_inputs(path,dest,delivery)
                self.assertEqual(out.read_bytes(),b'keep')
                self.assertEqual(other.read_bytes(),b'keep')

    def test_network_transfer_rejects_extra_bytes_and_cleans_temporary_container(self):
        api=self.api()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);path,dest,delivery=self.fixture(root)
            raw=path.read_bytes()+b'extra'
            with self.assertRaises(ValueError):
                api.fetch_inputs(dest,delivery,opener=lambda url:io.BytesIO(raw))
            self.assertEqual(list(dest.iterdir()),[])

    def test_exact_download_is_extracted_then_reused_without_another_transfer(self):
        api=self.api()
        with tempfile.TemporaryDirectory() as td:
            path,dest,delivery=self.fixture(Path(td))
            raw=path.read_bytes()
            rows=api.fetch_inputs(dest,delivery,opener=lambda url:io.BytesIO(raw))
            self.assertEqual(rows[0]['status'],'extracted')
            def unavailable(url):raise AssertionError('Verified inputs must not need another large download')
            self.assertEqual(api.fetch_inputs(dest,delivery,opener=unavailable)[0]['status'],'present')
            self.assertEqual(sorted(p.name for p in dest.iterdir()),['base-1.1-EN.xdelta'])

    def test_truncated_transfer_never_leaves_an_output_or_temporary_container(self):
        api=self.api()
        with tempfile.TemporaryDirectory() as td:
            path,dest,delivery=self.fixture(Path(td))
            with self.assertRaises(ValueError):
                api.fetch_inputs(dest,delivery,opener=lambda url:io.BytesIO(path.read_bytes()[:-1]))
            self.assertEqual(list(dest.iterdir()),[])

    def test_deadline_includes_last_data_read_and_end_of_file(self):
        api=self.api()
        for eof in (False,True):
            with self.subTest(eof=eof),tempfile.TemporaryDirectory() as td:
                path,dest,delivery=self.fixture(Path(td));now=[0]
                class Slow(io.BytesIO):
                    def read1(self,size):
                        chunk=super().read(size)
                        if (not chunk)==eof:now[0]=1801
                        return chunk
                with self.assertRaisesRegex(ValueError,'time limit'):
                    api.fetch_inputs(dest,delivery,opener=lambda url:Slow(path.read_bytes()),clock=lambda:now[0])
                self.assertEqual(list(dest.iterdir()),[])

    def test_explicit_http_mirror_keeps_the_tracked_https_delivery_pin(self):
        api=self.api()
        with tempfile.TemporaryDirectory() as td:
            path,dest,delivery=self.fixture(Path(td));original=json.loads(json.dumps(delivery))
            def local(url):
                self.assertEqual(url,'http://127.0.0.1:8123/release.zip')
                return io.BytesIO(path.read_bytes())
            rows=api.fetch_inputs(dest,delivery,url_override='http://127.0.0.1:8123/release.zip',opener=local)
            self.assertEqual(rows[0]['status'],'extracted')
            self.assertEqual((dest/'base-1.1-EN.xdelta').read_bytes(),b'owned build differences')
            self.assertEqual(delivery,original)
            delivery['url']='http://127.0.0.1:8123/release.zip'
            with self.assertRaises(ValueError):api.validate_delivery(delivery)


if __name__=='__main__':unittest.main()
