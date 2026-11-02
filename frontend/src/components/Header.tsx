interface HeaderProps {
  theme: string;
  onThemeChange: () => void;
}

function Header({ theme, onThemeChange }: HeaderProps) {
  return (
    <header className="dashboard-header">
      <div className="header-brand">
        <img
          src="/logo.png"
          alt="Geopolitical Risk Radar"
          className={`header-logo ${theme === "dark" ? "header-logo-dark" : ""}`}
        />

        <div>
          <h1>Geopolitical Risk Radar</h1>
          <p>
            Early-Warning &amp; Decision Support System for India&apos;s Crude-Oil
            Supply Chain
          </p>
        </div>
      </div>

      <button
        className="theme-toggle"
        onClick={onThemeChange}
        aria-label={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
        title={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
      >
        <span className={`theme-toggle-track ${theme}`}>
          <span className="theme-toggle-active" />

          <span className="theme-toggle-option theme-toggle-sun">
            <svg
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="3.5" />
              <path d="M12 2v2.5M12 19.5V22M4.93 4.93l1.77 1.77M17.3 17.3l1.77 1.77M2 12h2.5M19.5 12H22M4.93 19.07l1.77-1.77M17.3 6.7l1.77-1.77" />
            </svg>
          </span>

          <span className="theme-toggle-option theme-toggle-moon">
            <svg
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path d="M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5 8.5 8.5 0 1 0 20.5 14.5Z" />
            </svg>
          </span>
        </span>
      </button>
    </header>
  );
}

export default Header;