/* Sacred Gold Plus offline installer. Original application code: GPL-3.0-or-later. */
;(function () {
  'use strict';
  const MAX_BYTES = 256 * 1024 * 1024;
  const SOURCE_IDS = ['clean-us', 'plus-1.01', 'plus-1.02', 'plus-1.03',
                     'plus-1.04-en-plus', 'plus-1.04-en-classic',
                     'plus-1.04-it-plus', 'plus-1.04-it-classic'];
  /* One release per language, camera Plus: the camera never forms a name. */
  const GAME_NAME = {IT: 'Sacred Gold Plus 1.1 IT.nds', US: 'Sacred Gold Plus 1.1 EN.nds'};
  function validRecord(record) {
    return record && /^[a-f0-9]{64}$/.test(record.sha256) &&
      Number.isSafeInteger(record.bytes) && record.bytes > 0 && record.bytes <= MAX_BYTES;
  }
  function validateRelease(release) {
    const target = release && release.target;
    if (!release || release.schema !== 1 || release.version !== '1.1' || !validRecord(target) ||
        !['IT', 'US'].includes(target.language) || target.camera !== 'Plus' ||
        target.id !== (target.language === 'IT' ? 'it' : 'en') + '-plus' ||
        target.output_name !== GAME_NAME[target.language] ||
        !Array.isArray(release.sources) ||
        release.sources.length !== SOURCE_IDS.length) throw new Error('MANIFEST');
    const ids = new Set(), hashes = new Set();
    for (const source of release.sources) {
      if (!validRecord(source) || !SOURCE_IDS.includes(source.id) || ids.has(source.id) || hashes.has(source.sha256) ||
          typeof source.label !== 'string' || !source.label || !validRecord(source.patch) ||
          typeof source.patch.data !== 'string' || source.patch.data.length !== 4 * Math.ceil(source.patch.bytes / 3)) {
        throw new Error('MANIFEST');
      }
      ids.add(source.id); hashes.add(source.sha256);
    }
    return release;
  }
  async function digest(buffer) {
    if (!globalThis.crypto || !globalThis.crypto.subtle) throw new Error('CRYPTO');
    const bytes = await globalThis.crypto.subtle.digest('SHA-256', buffer);
    return Array.from(new Uint8Array(bytes), b => b.toString(16).padStart(2, '0')).join('');
  }
  async function classifyFile(file, release) {
    validateRelease(release);
    // Reject by advertised size before File.arrayBuffer allocates game-sized memory.
    if (!file || ![release.target.bytes, ...release.sources.map(s => s.bytes)].includes(file.size)) {
      throw new Error('UNKNOWN_SIZE');
    }
    if (!globalThis.crypto || !globalThis.crypto.subtle) throw new Error('CRYPTO');
    const buffer = await file.arrayBuffer();
    if (buffer.byteLength !== file.size) throw new Error('READ');
    const sha256 = await digest(buffer);
    if (sha256 === release.target.sha256 && buffer.byteLength === release.target.bytes) return {kind: 'current'};
    const source = release.sources.find(s => s.sha256 === sha256 && s.bytes === buffer.byteLength);
    if (!source) throw new Error('UNKNOWN_INPUT');
    return {kind: 'source', source, buffer};
  }
  const words = {
    en: {
      intro: 'Install or update this version. Everything happens offline in your browser.',
      privacy: 'Your game stays on this device. This tool creates a new file; it does not change your original game or open your saves.',
      choose: 'Choose your game file (.nds)', action: 'Check and create game', download: 'Download the verified game',
      help: 'Use original US HeartGold, a supported English Plus 1.01, 1.02 or 1.03, or any of the four 1.04 releases. Unknown or differently patched files are refused.',
      idle: 'Choose a game file to begin.', cancelled: 'The operation was interrupted. You can try again.', checking: 'Checking the complete game file…',
      working: 'Recognized: ', patch: 'Checking the included update…', decoding: 'Creating the updated game…',
      verifying: 'Checking the complete result…', ready: 'Verified. Download your new game below.',
      current: 'This file is already the exact version in this package. No update or new download is needed.',
      save: 'Keep your original game and a backup of its normal save. To continue, associate a copy of that save with the downloaded game in your emulator. Do not select a save file here.',
      credits: 'Decoder credits and MIT license', busy: 'Please keep this page open until verification finishes.',
      errors: {MANIFEST: 'The installer data is incomplete or inconsistent. Extract a fresh copy from the official package.',
        UNKNOWN_SIZE: 'This file size is not supported. Select the .nds game, not a ZIP or save.',
        UNKNOWN_INPUT: 'This game is not one of the supported exact versions. Your file has not been changed.',
        CRYPTO: 'This browser cannot verify local files securely. Open this HTML in a current desktop Chrome, Edge, Firefox or Safari browser; keep the original files.',
        BROWSER: 'This browser cannot run the offline installer. Open this HTML in a current desktop browser.',
        READ: 'The game could not be read completely. Select it again.',
        INPUT: 'The selected game did not pass verification. No result was created.',
        PATCH: 'The included update failed verification. Extract a fresh installer from the package.',
        OUTPUT: 'The result failed verification. No download is offered. Keep the original game.',
        DECODE: 'The update could not be completed. No download is offered. Try a current desktop browser with enough free memory.'}
    },
    it: {
      intro: 'Installa o aggiorna questa versione. Tutto avviene offline nel browser.',
      privacy: 'Il gioco resta su questo dispositivo. Lo strumento crea un nuovo file: non modifica il gioco originale e non apre i salvataggi.',
      choose: 'Scegli il file del gioco (.nds)', action: 'Controlla e crea il gioco', download: 'Scarica il gioco verificato',
      help: 'Usa HeartGold USA originale, una versione inglese supportata di Plus 1.01, 1.02 o 1.03, oppure una delle quattro uscite 1.04. I file sconosciuti o modificati diversamente vengono rifiutati.',
      idle: 'Scegli un gioco per iniziare.', cancelled: 'Operazione interrotta. Puoi riprovare.', checking: 'Controllo del file completo…',
      working: 'Riconosciuto: ', patch: 'Controllo dell’aggiornamento incluso…', decoding: 'Creazione del gioco aggiornato…',
      verifying: 'Controllo del risultato completo…', ready: 'Verificato. Scarica il nuovo gioco qui sotto.',
      current: 'Questo file è già esattamente la versione del pacchetto. Non serve aggiornarlo o scaricare una nuova copia.',
      save: 'Conserva il gioco originale e una copia del suo salvataggio normale. Per continuare, associa una copia di quel salvataggio al gioco scaricato nel tuo emulatore. Non selezionare un salvataggio qui.',
      credits: 'Crediti del decoder e licenza MIT', busy: 'Lascia aperta questa pagina fino al termine del controllo.',
      errors: {MANIFEST: 'I dati dell’installer sono incompleti o incoerenti. Estrai una nuova copia dal pacchetto ufficiale.',
        UNKNOWN_SIZE: 'La dimensione di questo file non è supportata. Seleziona il gioco .nds, non uno ZIP o un salvataggio.',
        UNKNOWN_INPUT: 'Questo gioco non corrisponde a una delle versioni esatte supportate. Il file non è stato modificato.',
        CRYPTO: 'Il browser non può verificare in modo sicuro i file locali. Apri questo HTML con una versione aggiornata di Chrome, Edge, Firefox o Safari su computer; conserva gli originali.',
        BROWSER: 'Il browser non può eseguire l’installer offline. Apri questo HTML con un browser aggiornato su computer.',
        READ: 'Non è stato possibile leggere tutto il gioco. Selezionalo di nuovo.',
        INPUT: 'Il gioco selezionato non ha superato il controllo. Nessun risultato è stato creato.',
        PATCH: 'L’aggiornamento incluso non ha superato il controllo. Estrai un nuovo installer dal pacchetto.',
        OUTPUT: 'Il risultato non ha superato il controllo. Non viene offerto alcun download. Conserva il gioco originale.',
        DECODE: 'Non è stato possibile completare l’aggiornamento. Non viene offerto alcun download. Prova un browser aggiornato su computer con memoria libera sufficiente.'}
    }
  };
  function mount(document) {
    const language = document.documentElement.lang.toLowerCase().startsWith('it') ? 'it' : 'en';
    const text = words[language];
    for (const node of document.querySelectorAll('[data-i18n]')) node.textContent = text[node.dataset.i18n];
    const file = document.getElementById('game-file'), button = document.getElementById('install');
    const status = document.getElementById('status'), download = document.getElementById('download');
    const progress = document.getElementById('progress');
    progress.setAttribute('aria-label', text.busy);
    let release, workerSource, activeWorker = null, workerURL = null, resultURL = null, busy = false, generation = 0;
    const show = message => { status.textContent = message; };
    function clearResult() {
      download.hidden = true; download.removeAttribute('href');
      if (resultURL) URL.revokeObjectURL(resultURL);
      resultURL = null;
    }
    function stopWorker() {
      if (activeWorker) activeWorker.terminate();
      if (workerURL) URL.revokeObjectURL(workerURL);
      activeWorker = null; workerURL = null;
    }
    function finish() {
      busy = false; progress.hidden = true; file.disabled = false; button.disabled = !file.files.length;
      document.getElementById('installer').setAttribute('aria-busy', 'false'); stopWorker();
    }
    function fail(code) { clearResult(); show(text.errors[code] || text.errors.DECODE); finish(); }
    try {
      release = validateRelease(JSON.parse(document.getElementById('release-data').textContent));
      workerSource = JSON.parse(document.getElementById('worker-source').textContent);
      if (typeof workerSource !== 'string' || !workerSource) throw new Error('MANIFEST');
      if (!globalThis.crypto || !globalThis.crypto.subtle) throw new Error('CRYPTO');
      if (typeof Worker !== 'function' || typeof Blob !== 'function' || typeof File.prototype.arrayBuffer !== 'function') throw new Error('BROWSER');
    } catch (error) {
      show(text.errors[error.message] || text.errors.MANIFEST); button.disabled = true; file.disabled = true; return;
    }
    show(text.idle);
    file.addEventListener('change', () => { if (!busy) { clearResult(); button.disabled = !file.files.length; show(text.idle); } });
    button.addEventListener('click', async () => {
      if (busy || !file.files.length) return;
      const operation = ++generation;
      const isCurrent = () => operation === generation;
      busy = true; clearResult(); button.disabled = true; file.disabled = true; progress.hidden = false;
      document.getElementById('installer').setAttribute('aria-busy', 'true'); show(text.checking);
      try {
        const selected = await classifyFile(file.files[0], release);
        if (!isCurrent()) return;
        if (selected.kind === 'current') { show(text.current); finish(); return; }
        show(text.working + selected.source.label + '. ' + text.busy);
        workerURL = URL.createObjectURL(new Blob([workerSource], {type: 'text/javascript'}));
        const worker = new Worker(workerURL);
        activeWorker = worker;
        worker.onerror = event => {
          event.preventDefault();
          if (isCurrent() && activeWorker === worker) fail('DECODE');
        };
        worker.onmessage = event => {
          if (!isCurrent() || activeWorker !== worker) return;
          const message = event.data;
          if (message.type === 'progress') { show(text[message.stage] || text.busy); return; }
          if (message.type === 'error') { fail(message.code); return; }
          if (message.type !== 'ready' || !(message.buffer instanceof ArrayBuffer) || message.buffer.byteLength !== release.target.bytes) { fail('OUTPUT'); return; }
          resultURL = URL.createObjectURL(new Blob([message.buffer], {type: 'application/octet-stream'}));
          download.href = resultURL; download.download = release.target.output_name;
          download.hidden = false; show(text.ready); finish(); download.focus();
        };
        worker.postMessage({input: selected.buffer, source: selected.source, target: release.target}, [selected.buffer]);
      } catch (error) { if (isCurrent()) fail(error.message); }
    });
    globalThis.addEventListener('pagehide', () => {
      const interrupted = busy;
      // File reads and Web Crypto promises cannot be aborted. Invalidate their
      // callbacks before releasing the worker and resetting a BFCache page.
      generation++;
      clearResult(); finish();
      show(interrupted ? text.cancelled : text.idle);
    });
    globalThis.addEventListener('pageshow', () => {
      // A browser may restore form state after pagehide, including disabled
      // controls or a cleared file selection. Reconcile it without starting work.
      if (!busy) finish();
    });
  }
  if (typeof module === 'object' && module.exports) module.exports = {validateRelease, classifyFile};
  if (typeof document === 'object') mount(document);
}());
