/* Application wrapper only; the three preceding MIT vendor files are unchanged. */
;(function () {
  'use strict';
  const MAX_BYTES = 256 * 1024 * 1024;
  function valid(record) {
    return record && /^[a-f0-9]{64}$/.test(record.sha256) && Number.isSafeInteger(record.bytes) && record.bytes > 0 && record.bytes <= MAX_BYTES;
  }
  async function digest(buffer) {
    if (!globalThis.crypto || !globalThis.crypto.subtle) throw new Error('CRYPTO');
    const result = await globalThis.crypto.subtle.digest('SHA-256', buffer);
    return Array.from(new Uint8Array(result), b => b.toString(16).padStart(2, '0')).join('');
  }
  self.onmessage = async function (event) {
    try {
      const job = event.data;
      if (!job || !valid(job.source) || !valid(job.target) || !valid(job.source.patch)) throw new Error('MANIFEST');
      if (!(job.input instanceof ArrayBuffer) || job.input.byteLength !== job.source.bytes || await digest(job.input) !== job.source.sha256) throw new Error('INPUT');
      self.postMessage({type: 'progress', stage: 'patch'});
      const patch = job.source.patch;
      if (typeof patch.data !== 'string' || patch.data.length !== 4 * Math.ceil(patch.bytes / 3) ||
          !/^[A-Za-z0-9+/]*={0,2}$/.test(patch.data)) throw new Error('PATCH');
      let binary;
      try { binary = atob(patch.data); } catch (_) { throw new Error('PATCH'); }
      if (binary.length !== patch.bytes) throw new Error('PATCH');
      const patchBytes = Uint8Array.from(binary, character => character.charCodeAt(0));
      binary = null;
      if (await digest(patchBytes.buffer) !== patch.sha256 || patchBytes.length < 5 ||
          ![0xd6, 0xc3, 0xc4, 0, 0].every((value, index) => patchBytes[index] === value)) throw new Error('PATCH');
      self.postMessage({type: 'progress', stage: 'decoding'});
      // The pinned module's optional Adler path expects an external legacy
      // helper. Instead enforce full SHA-256 and byte count on the entire output.
      const result = VCDIFF.fromFile(new BinFile(patchBytes.buffer)).apply(new BinFile(job.input), false);
      if (result.fileSize !== job.target.bytes || result._u8array.byteLength !== job.target.bytes) throw new Error('OUTPUT');
      self.postMessage({type: 'progress', stage: 'verifying'});
      const output = result._u8array.buffer;
      if (output.byteLength !== job.target.bytes || await digest(output) !== job.target.sha256) throw new Error('OUTPUT');
      self.postMessage({type: 'ready', buffer: output}, [output]);
    } catch (error) {
      const known = ['CRYPTO', 'MANIFEST', 'INPUT', 'PATCH', 'OUTPUT'];
      self.postMessage({type: 'error', code: known.includes(error.message) ? error.message : 'DECODE'});
    }
  };
}());
