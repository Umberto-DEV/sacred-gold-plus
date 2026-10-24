#!/usr/bin/env node
// Apply through the unmodified Rom Patcher JS public API, then verify both SHA-256s.
// Usage: node verify-rompatcher.cjs RPJS_DIR SOURCE PATCH SOURCE_SHA256 TARGET_SHA256 OUTPUT
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const [repo, sourcePath, patchPath, sourceHash, targetHash, outputPath] = process.argv.slice(2);
const sha256 = bytes => crypto.createHash('sha256').update(bytes).digest('hex');

try {
    if (process.argv.length !== 8 || !/^[0-9a-f]{64}$/i.test(sourceHash || '') || !/^[0-9a-f]{64}$/i.test(targetHash || '')) {
        throw new Error('Usage: node verify-rompatcher.cjs RPJS_DIR SOURCE PATCH SOURCE_SHA256 TARGET_SHA256 OUTPUT');
    }
    if (fs.existsSync(outputPath)) throw new Error('Output already exists; choose a new path');
    const BinaryFile = require(path.resolve(repo, 'rom-patcher-js/modules/BinFile.js'));
    const patcher = require(path.resolve(repo, 'rom-patcher-js/RomPatcher.js'));
    const source = new BinaryFile(sourcePath);
    const sourceSha = sha256(source._u8array);
    if (sourceSha !== sourceHash.toLowerCase()) throw new Error('Source SHA-256 mismatch');
    const patchFile = new BinaryFile(patchPath);
    const patch = patcher.parsePatchFile(patchFile);
    if (!patch) throw new Error('Unrecognized patch format');
    const result = patcher.applyPatch(source, patch, {
        requireValidation: true,
        removeHeader: false,
        addHeader: false,
        fixChecksum: false,
        outputSuffix: false
    });
    // VCDIFF in this RPJS revision has no validateSource method, so the explicit
    // whole-file hashes above and below are essential even with requireValidation.
    const resultSha = sha256(result._u8array);
    if (resultSha !== targetHash.toLowerCase()) throw new Error('Target SHA-256 mismatch');
    fs.writeFileSync(outputPath, result._u8array, { flag: 'wx' });
    console.log(JSON.stringify({ result: 'PASS', patch: path.basename(patchPath), patch_sha256: sha256(patchFile._u8array), source_sha256: sourceSha, target_sha256: resultSha, bytes: result.fileSize }));
} catch (error) {
    console.log(JSON.stringify({ result: 'FAIL', patch: patchPath ? path.basename(patchPath) : null, error: error.message }));
    process.exitCode = 1;
}
