/**
 * VIKARMA — Electron Main Process
 * The Sacred Gateway — where code meets consciousness
 * 
 * 🔱 Om Namah Shivaya
 * The Vikarma Team
 */

const { app, BrowserWindow, ipcMain, shell, Tray, Menu, nativeImage } = require('electron')
const path = require('path')
const { spawn } = require('child_process')
const Store = require('electron-store')

const store = new Store()
const isDev = process.env.NODE_ENV === 'development'
const PORT = process.env.PORT || 3000

let mainWindow = null
let tray = null
let pythonServer = null

// ── Create Main Window ─────────────────────────────────────────────────────

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
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

  // Load app
  const url = isDev
    ? `http://localhost:${PORT}`
    : `file://${path.join(__dirname, '../src/out/index.html')}`

  mainWindow.loadURL(url)

  // Show when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show()
    if (isDev) mainWindow.webContents.openDevTools()
  })

  // Handle external links
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url)
    return { action: 'deny' }
  })

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

// ── System Tray ────────────────────────────────────────────────────────────

function createTray() {
  const iconPath = path.join(__dirname, '../public/tray-icon.png')
  tray = new Tray(nativeImage.createFromPath(iconPath).resize({ width: 16, height: 16 }))

  const contextMenu = Menu.buildFromTemplate([
    { label: '🔱 Vikarma', enabled: false },
    { type: 'separator' },
    { label: '👁️ Show', click: () => mainWindow?.show() },
    { label: '🏛️ Temples', click: () => mainWindow?.webContents.send('navigate', '/temples') },
    { label: '🌍 Monitor', click: () => mainWindow?.webContents.send('navigate', '/monitor') },
    { type: 'separator' },
    { label: '⚙️ Settings', click: () => mainWindow?.webContents.send('navigate', '/settings') },
    { type: 'separator' },
    { label: '🕉️ Quit', click: () => { app.quit() } },
  ])

  tray.setToolTip('Vikarma — Free AI for All Humanity 🔱')
  tray.setContextMenu(contextMenu)
  tray.on('click', () => {
    mainWindow?.isVisible() ? mainWindow.hide() : mainWindow?.show()
  })
}

// ── Python MCP Server ──────────────────────────────────────────────────────

function startPythonServer() {
  const serverPath = path.join(__dirname, '../server/main.py')
  pythonServer = spawn('python3', [serverPath], {
    env: { ...process.env },
    stdio: ['pipe', 'pipe', 'pipe'],
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
