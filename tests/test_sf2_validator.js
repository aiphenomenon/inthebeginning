/**
 * Unit test for the SpessaBridge._validateSoundFontBuffer logic.
 *
 * Mirrors the static method in deploy/v13/inthebeginning-bounce/js/
 * spessa-bridge.js — keep in sync. The validator catches three failure
 * modes for the SF2 file served from the game:
 *   1. Too small / empty buffer
 *   2. Git LFS pointer text (first 4 bytes "vers" from "version")
 *   3. Non-RIFF header (e.g. HTML error page)
 *
 * Run with: node tests/test_sf2_validator.js
 */

function validateSoundFontBuffer(buffer, url) {
  var MIN_SF2_BYTES = 1000000;
  if (!buffer || buffer.byteLength < 4) {
    throw new Error(
      'SoundFont too small or empty: ' + (buffer ? buffer.byteLength : 0) +
      ' bytes from ' + url + '. Expected a multi-megabyte .sf2 file.'
    );
  }
  var header = new Uint8Array(buffer, 0, 4);
  var magic = String.fromCharCode(header[0], header[1], header[2], header[3]);
  if (magic === 'vers') {
    var pointerText = new TextDecoder().decode(new Uint8Array(buffer, 0, Math.min(200, buffer.byteLength)));
    throw new Error(
      'SoundFont at ' + url + ' is a Git LFS pointer file, not the actual .sf2 binary. ' +
      'GitHub Pages is serving the pointer text instead of resolving it through LFS. ' +
      'Fix: enable Git LFS on the Pages repo and ensure LFS objects are pushed, ' +
      'or commit the .sf2 outside of LFS. Pointer content: ' + pointerText.substring(0, 120) + '...'
    );
  }
  if (magic !== 'RIFF') {
    throw new Error('SoundFont at ' + url + ' has invalid magic bytes: expected "RIFF" but got "' + magic + '".');
  }
  if (buffer.byteLength < MIN_SF2_BYTES) {
    throw new Error('SoundFont at ' + url + ' is suspiciously small: ' + buffer.byteLength + ' bytes (expected > ' + MIN_SF2_BYTES + ').');
  }
}

var pass = 0, fail = 0;
function t(name, fn) {
  try { fn(); pass++; console.log('PASS: ' + name); }
  catch (e) { fail++; console.log('FAIL: ' + name + ' — ' + e.message); }
}
function expectThrow(fn, needle) {
  try { fn(); throw new Error('expected throw'); }
  catch (e) {
    if (!e.message.includes(needle))
      throw new Error('expected message to include "' + needle + '" but got: ' + e.message);
  }
}
function buf(bytes) {
  var b = new ArrayBuffer(bytes.length);
  new Uint8Array(b).set(bytes);
  return b;
}
function strbuf(s) {
  var arr = [];
  for (var i = 0; i < s.length; i++) arr.push(s.charCodeAt(i));
  return buf(arr);
}

t('null buffer is rejected as too small', function () {
  expectThrow(function () { validateSoundFontBuffer(null, '/foo.sf2'); }, 'too small or empty');
});

t('2-byte buffer is rejected as too small', function () {
  expectThrow(function () { validateSoundFontBuffer(buf([82, 73]), '/foo.sf2'); }, 'too small or empty');
});

t('LFS pointer is detected with specific message', function () {
  var pointer = 'version https://git-lfs.github.com/spec/v1\noid sha256:abc\nsize 148930764\n';
  expectThrow(function () { validateSoundFontBuffer(strbuf(pointer), '/sf.sf2'); }, 'Git LFS pointer file');
});

t('HTML response is rejected (not RIFF)', function () {
  var html = '<!DOCTYPE html>\n<html>...' + new Array(2000).join('x');
  expectThrow(function () { validateSoundFontBuffer(strbuf(html), '/sf.sf2'); }, 'invalid magic bytes');
});

t('RIFF header with too-small body is rejected', function () {
  var arr = new Array(100).fill(0);
  arr[0] = 82; arr[1] = 73; arr[2] = 70; arr[3] = 70;
  expectThrow(function () { validateSoundFontBuffer(buf(arr), '/sf.sf2'); }, 'suspiciously small');
});

t('valid RIFF with plausible size passes', function () {
  var arr = new Array(2000000).fill(0);
  arr[0] = 82; arr[1] = 73; arr[2] = 70; arr[3] = 70;
  validateSoundFontBuffer(buf(arr), '/sf.sf2');
});

console.log('');
console.log(pass + ' passed, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
