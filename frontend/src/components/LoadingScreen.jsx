export default function LoadingScreen() {
  return (
    <div className="startup-loader" role="status" aria-live="polite" aria-label="Loading">
      <img
        src="https://github.githubassets.com/images/mona-loading-dark.gif"
        alt="Loading"
        width="64"
        height="64"
      />
      <div className="startup-loader__text">just a moment</div>
      <small style={{ position: 'fixed', right: 12, bottom: 10, opacity: 0.55 }}>loading screen by my friend ;)</small>
    </div>
  )
}
