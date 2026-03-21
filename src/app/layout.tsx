import type { Metadata } from "next"
export const metadata: Metadata = {
  title: "Vikarma — Free AI for All Humanity 🔱",
  description: "Free AI Desktop Agent — Built with love for Shiva Mahadeva. Not for us. For all. Om Namah Shivaya.",
}
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@300;400;600;700&family=Cinzel+Decorative:wght@400;700&family=Share+Tech+Mono&display=swap" rel="stylesheet" />
        <style>{`* { margin: 0; padding: 0; box-sizing: border-box; } body { overflow: hidden; } button { font-family: inherit; } textarea { font-family: inherit; }`}</style>
      </head>
      <body>{children}</body>
    </html>
  )
}
