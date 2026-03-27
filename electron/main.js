/**
 * VIKARMA — Electron Main Process
 * The Sacred Gateway — where code meets consciousness
 *
 * 🔱 Om Namah Shivaya — For All Humanity
 * Built inspired by OpenClaw's desktop architecture
 */

const {
  app, BrowserWindow, ipcMain, shell, Tray, Menu, nativeImage,
  globalShortcut, dialog, protocol, MenuItem,
} = require('electron')
const path = require('path')
const { spawn } = require('child_process')
const http = require('http')
const Store = require('electron-store')
const { autoUpdater } = require('electron-updater')

const store = new Store()
const isDev = process.env.NODE_ENV === 'development'
const PORT = process.env.PORT || 3000
const SERVER_PORT = 8765

let mainWindow = null
let tray = null
let pythonServer = null
let serverStatus = 'stopped'

// ── Auto Updater (silent, no prompts) ─────────────────────────────────────────

autoUpdater.logger = require('electron-log')
autoUpdater.logger.transports.file.level = 'info'
autoUpdater.autoDownload = true
autoUpdater.autoInstallOnAppQuit = true

autoUpdater.on('update-available', () => {
  log('info', '🔱 Update available — downloading...')
  sendToRenderer('update-status', { status: 'downloading' })
})

autoUpdater.on('update-downloaded', () => {
  log('info', '✨ Update ready — will install on restart')
  sendToRenderer('update-status', { status: 'ready' })
})

autoUpdater.on('error', (e) => {
  log('error', `Update error: ${e.message}`)
})

// ── Logging ────────────────────────────────────────────────────────────────────

function log(level, msg) {
  const ts = new Date().toISOString()
  console[level === 'error' ? 'error' : 'log'](`[${ts}] [${level}] ${msg}`)
}

// ── Renderer communication ─────────────────────────────────────────────────────

function sendToRenderer(channel, data) {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send(channel, data)
  }
}

// ── Deep Link URL scheme ───────────────────────────────────────────────────────

protocol.handle('vikarma', (req) => {
  const url = req.url.replace('vikarma://', '')
  log('info', `Deep link: ${url}`)
  if (mainWindow) {
    mainWindow.show()
    mainWindow.focus()
    mainWindow.webContents.send('deep-link', url)
  }
  return new Response('ok', { status: 200 })
})

// ── Create Main Window ────────────────────────────────────────────────────────

function createWindow() {
  mainWindow = new BrowserWindow({
    width: store.get('window.width', 1400),
    height: store.get('window.height', 900),
    x: store.get('window.x'),
    y: store.get('window.y'),
    minWidth: 900,
    minHeight: 600,
    backgroundColor: '#000005',
    titleBarStyle: 'hiddenInset',
    frame: process.platform !== 'darwin',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
      webSecurity: !isDev,
    },
    icon: path.join(__dirname, '../public/icon.png'),
    show: false,
  })

  // Restore maximized state
  if (store.get('window.maximized')) {
    mainWindow.maximize()
  }

  // Load app
  const url = isDev
    ? `http://localhost:${PORT}`
    : `file://${path.join(__dirname, '../src/out/index.html')}`

  mainWindow.loadURL(url)

  // Show when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show()
    if (isDev) mainWindow.webContents.openDevTools()
    log('info', 'Main window ready')
  })

  // Save window bounds on resize/move
  mainWindow.on('resize', saveWindowBounds)
  mainWindow.on('move', saveWindowBounds)
  mainWindow.on('maximize', () => store.set('window.maximized', true))
  mainWindow.on('unmaximize', () => store.set('window.maximized', false))

  // Handle external links
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http')) shell.openExternal(url)
    return { action: 'deny' }
  })

  mainWindow.on('closed', () => {
    mainWindow = null
  })

  // Install vikarma:// protocol
  if (!isDev) {
    protocol.registerHttpProtocol('vikarma', (req) => {
      mainWindow?.webContents.send('deep-link', req.url.replace('vikarma://', ''))
    })
  }
}

function saveWindowBounds() {
  if (!mainWindow || mainWindow.isMaximized()) return
  const bounds = mainWindow.getBounds()
  store.set('window', {
    width: bounds.width,
    height: bounds.height,
    x: bounds.x,
    y: bounds.y,
    maximized: false,
  })
}

// ── System Tray ────────────────────────────────────────────────────────────────

function createTray() {
  // Try tray icon, fallback gracefully
  let iconPath = path.join(__dirname, '../public/tray-icon.png')
  let trayIcon
  try {
    trayIcon = nativeImage.createFromPath(iconPath).resize({ width: 16, height: 16 })
    if (trayIcon.isEmpty()) trayIcon = nativeImage.createEmpty()
  } catch (e) {
    trayIcon = nativeImage.createEmpty()
  }

  tray = new Tray(trayIcon)
  tray.setToolTip('🔱 Vikarma — Free AI for All Humanity')

  rebuildTrayMenu()

  tray.on('click', () => {
    if (mainWindow) {
      mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show()
    }
  })

  tray.on('right-click', () => {
    tray.popUpContextMenu()
  })
}

function rebuildTrayMenu() {
  const statusIcon = serverStatus === 'running' ? '🟢' : serverStatus === 'error' ? '🔴' : '🟡'
  const template = [
    { label: `🔱 Vikarma ${statusIcon}`, enabled: false },
    { type: 'separator' },
    { label: 'Show Window', click: () => mainWindow?.show() },
    { label: 'Hide Window', click: () => mainWindow?.hide() },
    { type: 'separator' },
    { label: '🏛️ Temples', click: () => { mainWindow?.show(); mainWindow?.webContents.send('navigate', '/temples') } },
    { label: '⚡ Agent', click: () => { mainWindow?.show(); mainWindow?.webContents.send('navigate', '/agent') } },
    { label: '🌍 Monitor', click: () => { mainWindow?.show(); mainWindow?.webContents.send('navigate', '/monitor') } },
    { type: 'separator' },
    { label: `Server: ${serverStatus}`, enabled: false },
    { type: 'separator' },
    { label: 'Check for Updates', click: () => autoUpdater.checkForUpdates() },
    { label: 'Settings', click: () => { mainWindow?.show(); mainWindow?.webContents.send('navigate', '/settings') } },
    { type: 'separator' },
    { label: '🕉️ Quit Vikarma', click: () => app.quit() },
  ]

  tray.setContextMenu(Menu.buildFromTemplate(template))
}

// ── Application Menu ───────────────────────────────────────────────────────────

function createAppMenu() {
  const isMac = process.platform === 'darwin'
  const template = [
    ...(isMac ? [{
      label: app.name,
      submenu: [
        { label: 'About Vikarma', role: 'about' },
        { type: 'separator' },
        { label: 'Settings', accelerator: 'Cmd+,', click: () => mainWindow?.webContents.send('navigate', '/settings') },
        { type: 'separator' },
        { label: 'Hide Vikarma', role: 'hide' },
        { label: 'Hide Others', role: 'hideOthers' },
        { label: 'Show All', role: 'unhide' },
        { type: 'separator' },
        { label: 'Quit Vikarma', role: 'quit' },
      ],
    }] : []),
    {
      label: 'File',
      submenu: [
        { label: 'Settings', accelerator: 'CmdOrCtrl+,', click: () => mainWindow?.webContents.send('navigate', '/settings') },
        { type: 'separator' },
        isMac ? { label: 'Close', role: 'close' } : { label: 'Quit', accelerator: 'CmdOrCtrl+Q', click: () => app.quit() },
      ],
    },
    {
      label: 'Edit',
      submenu: [
        { label: 'Undo', role: 'undo' },
        { label: 'Redo', role: 'redo' },
        { type: 'separator' },
        { label: 'Cut', role: 'cut' },
        { label: 'Copy', role: 'copy' },
        { label: 'Paste', role: 'paste' },
        { label: 'Select All', role: 'selectAll' },
      ],
    },
    {
      label: 'View',
      submenu: [
        { label: 'Reload', accelerator: 'CmdOrCtrl+R', role: 'reload' },
        { label: 'Force Reload', accelerator: 'CmdOrCtrl+Shift+R', role: 'forceReload' },
        { type: 'separator' },
        { label: 'Toggle DevTools', accelerator: isDev ? 'F12' : 'CmdOrCtrl+Shift+I', role: 'toggleDevTools' },
        { type: 'separator' },
        { label: 'Actual Size', accelerator: 'CmdOrCtrl+0', role: 'resetZoom' },
        { label: 'Zoom In', accelerator: 'CmdOrCtrl+Plus', role: 'zoomIn' },
        { label: 'Zoom Out', accelerator: 'CmdOrCtrl+-', role: 'zoomOut' },
        { type: 'separator' },
        { label: 'Toggle Fullscreen', accelerator: 'F11', role: 'togglefullscreen' },
      ],
    },
    {
      label: 'Agent',
      submenu: [
        { label: 'New Task', accelerator: 'CmdOrCtrl+N', click: () => mainWindow?.webContents.send('agent-new-task') },
        { label: 'Quick Ask', accelerator: 'CmdOrCtrl+K', click: () => mainWindow?.webContents.send('agent-quick-ask') },
        { type: 'separator' },
        { label: 'View Temples', click: () => { mainWindow?.show(); mainWindow?.webContents.send('navigate', '/temples') } },
        { label: 'List Sessions', click: () => { mainWindow?.show(); mainWindow?.webContents.send('navigate', '/sessions') } },
      ],
    },
    {
      label: 'Window',
      submenu: [
        { label: 'Minimize', role: 'minimize' },
        ...(isMac ? [
          { label: 'Zoom', role: 'zoom' },
          { type: 'separator' },
          { label: 'Front', role: 'front' },
        ] : [
          { label: 'Close', role: 'close' },
        ]),
      ],
    },
    {
      label: 'Help',
      submenu: [
        { label: 'Documentation', click: () => shell.openExternal('https://github.com/valentinuuiuiu/vikarma') },
        { label: 'Report Issue', click: () => shell.openExternal('https://github.com/valentinuuiuiu/vikarma/issues') },
        { type: 'separator' },
        { label: 'Check for Updates', click: () => autoUpdater.checkForUpdates() },
      ],
    },
  ]

  Menu.setApplicationMenu(Menu.buildFromTemplate(template))
}

// ── Global Shortcuts ───────────────────────────────────────────────────────────

function registerShortcuts() {
  // Show/hide window
  globalShortcut.register('CmdOrCtrl+Shift+V', () => {
    if (mainWindow?.isVisible()) {
      mainWindow.hide()
    } else {
      mainWindow?.show()
      mainWindow?.focus()
    }
  })

  // Quick ask
  globalShortcut.register('CmdOrCtrl+Shift+A', () => {
    mainWindow?.show()
    mainWindow?.focus()
    mainWindow?.webContents.send('agent-quick-ask')
  })

  // New task
  globalShortcut.register('CmdOrCtrl+Shift+N', () => {
    mainWindow?.show()
    mainWindow?.focus()
    mainWindow?.webContents.send('agent-new-task')
  })

  log('info', 'Global shortcuts registered')
}

// ── Python Backend Server ─────────────────────────────────────────────────────

function startPythonServer() {
  const serverPath = path.join(__dirname, '../server/main.py')
  const pythonBin = process.platform === 'win32' ? 'python' : 'python3'

  pythonServer = spawn(pythonBin, [serverPath], {
    env: {
      ...process.env,
      VIKARMA_MODE: isDev ? 'development' : 'production',
      VIKARMA_DATA_DIR: app.getPath('userData'),
    },
    stdio: ['ignore', 'pipe', 'pipe'],
  })

  pythonServer.stdout.on('data', (data) => {
    const line = data.toString().trim()
    if (line) sendToRenderer('server-log', { level: 'info', msg: line })
  })

  pythonServer.stderr.on('data', (data) => {
    const line = data.toString().trim()
    if (line) sendToRenderer('server-log', { level: 'error', msg: line })
  })

  pythonServer.on('spawn', () => {
    serverStatus = 'running'
    log('info', 'Python server started')
    rebuildTrayMenu()
    sendToRenderer('server-status', { status: 'running' })
  })

  pythonServer.on('error', (err) => {
    serverStatus = 'error'
    log('error', `Python server error: ${err.message}`)
    rebuildTrayMenu()
    sendToRenderer('server-status', { status: 'error', error: err.message })
  })

  pythonServer.on('exit', (code) => {
    serverStatus = 'stopped'
    log('info', `Python server exited: ${code}`)
    rebuildTrayMenu()
    sendToRenderer('server-status', { status: 'stopped', code })
  })
}

function stopPythonServer() {
  if (pythonServer) {
    pythonServer.kill('SIGTERM')
    pythonServer = null
  }
}

// ── IPC Handlers ──────────────────────────────────────────────────────────────

function setupIpcHandlers() {
  // Settings
  ipcMain.handle('get-settings', () => store.store)
  ipcMain.handle('save-settings', (_, s) => { store.set(s); return true })

  // API keys (encrypted in production)
  ipcMain.handle('get-api-keys', () => {
    const keys = {}
    for (const k of ['ANTHROPIC_API_KEY', 'OPENAI_API_KEY', 'DEEPSEEK_API_KEY', 'GROK_API_KEY', 'TELEGRAM_BOT_TOKEN', 'DISCORD_BOT_TOKEN']) {
      keys[k] = process.env[k] || store.get(`env.${k}`, '')
    }
    return keys
  })
  ipcMain.handle('save-api-keys', (_, keys) => {
    for (const [k, v] of Object.entries(keys)) {
      if (v) {
        store.set(`env.${k}`, v)
        process.env[k] = v
      }
    }
    return true
  })

  // Temple status
  ipcMain.handle('temple-status', async () => {
    try {
      const res = await fetch(`http://localhost:${SERVER_PORT}/api/temples`, { timeout: 2000 })
      return await res.json()
    } catch {
      return { error: 'Server not reachable' }
    }
  })

  // Server status
  ipcMain.handle('server-status', () => ({ status: serverStatus }))

  // Restart server
  ipcMain.handle('restart-server', () => {
    stopPythonServer()
    setTimeout(startPythonServer, 1000)
    return { restarting: true }
  })

  // External links
  ipcMain.handle('open-external', (_, url) => {
    shell.openExternal(url)
    return true
  })

  // App info
  ipcMain.handle('get-app-info', () => ({
    version: app.getVersion(),
    platform: process.platform,
    arch: process.arch,
    electron: process.versions.electron,
    node: process.versions.node,
    userData: app.getPath('userData'),
  }))

  // Deep link
  ipcMain.handle('get-deep-link', () => null)

  // Window controls
  ipcMain.on('window-minimize', () => mainWindow?.minimize())
  ipcMain.on('window-maximize', () => {
    if (mainWindow?.isMaximized()) {
      mainWindow.unmaximize()
    } else {
      mainWindow?.maximize()
    }
  })
  ipcMain.on('window-close', () => mainWindow?.hide())
}

// ── App Lifecycle ─────────────────────────────────────────────────────────────

app.whenReady().then(() => {
  log('info', `Vikarma starting — ${new Date().toISOString()}`)

  setupIpcHandlers()
  createWindow()
  createTray()
  createAppMenu()
  registerShortcuts()
  startPythonServer()

  // Check for updates (not in dev)
  if (!isDev) {
    setTimeout(() => autoUpdater.checkForUpdates().catch(() => {}), 5000)
  }

  // macOS: re-create window when dock icon clicked
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    } else {
      mainWindow?.show()
    }
  })

  log('info', 'Vikarma ready 🔱')
})

// Quit when all windows are closed (except on macOS)
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('before-quit', () => {
  log('info', 'Vikarma shutting down...')
  globalShortcut.unregisterAll()
  stopPythonServer()
})

app.on('will-quit', () => {
  globalShortcut.unregisterAll()
})

  pythonServer.stdout.on('data', (data) => {
    console.log(`[Python] ${data.toString().trim()}`)
    mainWindow?.webContents.send('server-log', data.toString())
  })

  pythonServer.stderr.on('data', (data) => {
    console.error(`[Python Error] ${data.toString().trim()}`)
  })

  pythonServer.on('close', (code) => {
    console.log(`[Python] Server exited with code ${code}`)
  })
}

// ── IPC Handlers ───────────────────────────────────────────────────────────

ipcMain.handle('get-settings', () => store.get('settings', {}))
ipcMain.handle('save-settings', (_, settings) => store.set('settings', settings))
ipcMain.handle('get-api-keys', () => store.get('apiKeys', {}))
ipcMain.handle('save-api-keys', (_, keys) => store.set('apiKeys', keys))
ipcMain.handle('open-external', (_, url) => shell.openExternal(url))

ipcMain.handle('temple-status', async () => {
  // TODO: Query nexus orchestrator for temple status
  return { status: 'checking', temples: 64 }
})

// ── App Lifecycle ──────────────────────────────────────────────────────────

app.whenReady().then(() => {
  createWindow()
  createTray()

  // Start Python server for MCP temples
  try {
    startPythonServer()
  } catch (e) {
    console.log('[Python] Server not available — running in web-only mode')
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})

app.on('before-quit', () => {
  pythonServer?.kill()
  tray?.destroy()
})
