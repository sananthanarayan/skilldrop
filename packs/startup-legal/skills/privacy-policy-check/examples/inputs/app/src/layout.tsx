export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <script async src="https://connect.facebook.net/en_US/fbevents.js"></script>
        <script dangerouslySetInnerHTML={{ __html: "fbq('init', 'PIXEL_ID'); fbq('track', 'PageView');" }} />
      </head>
      <body>{children}</body>
    </html>
  );
}
