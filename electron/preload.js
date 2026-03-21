/**
 * VIKARMA — Electron Preload
 * Sacred bridge between Electron and the web layer
 * 🔱 Om Namah Shivaya
 */

const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('vikarma', {
  // Settings
  getSettings: () => ipcRenderer.invoke('get-settings'),
  saveSettings: (s) => ipcRenderer.invoke('save-settings', s),
  getApiKeys: () => ipcRenderer.invoke('get-api-keys'),
  saveApiKeys: (k) => ipcRenderer.invoke('save-api-keys', k),

  // Navigation from tray
  onNavigate: (cb) => ipcRenderer.on('navigate', (_, route) => cb(route)),

  // Temple status
  templeStatus: () => ipcRenderer.invoke('temple-status'),

  // Server logs
  onServerLog: (cb) => ipcRenderer.on('server-log', (_, log) => cb(log)),

  // External links
  openExternal: (url) => ipcRenderer.invoke('open-external', url),

  // Platform info
  platform: process.platform,
  version: process.env.npm_package_version || '1.0.0',
})
