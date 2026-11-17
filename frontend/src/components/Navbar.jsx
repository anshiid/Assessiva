
import { useState } from "react";
import { BookOpen, Menu, X } from "lucide-react";

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);

  const closeMenu = () => setMenuOpen(false);

  return (
    <header className="site-header">
      <nav className="navbar" aria-label="Main navigation">
        <a className="brand" href="#home" aria-label="Assessiva home" onClick={closeMenu}>
          <span className="brand-icon"><BookOpen size={21} /></span>
          <span className="brand-name">Assessiva</span>
          <span className="brand-caption">TEACHER STUDIO</span>
        </a>

        <div className={`nav-links${menuOpen ? " is-open" : ""}`} id="primary-navigation">
          <a href="#home" onClick={closeMenu}>Overview</a>
          <a href="#evaluation" onClick={closeMenu}>New assessment</a>
          <a href="#about" onClick={closeMenu}>Our approach</a>
        </div>

        <a className="nav-action" href="#evaluation">
          Start a review <span aria-hidden="true">↗</span>
        </a>

        <button
          className="mobile-menu"
          type="button"
          aria-label={menuOpen ? "Close navigation menu" : "Open navigation menu"}
          aria-expanded={menuOpen}
          aria-controls="primary-navigation"
          onClick={() => setMenuOpen((open) => !open)}
        >
          {menuOpen ? <X size={21} /> : <Menu size={21} />}
        </button>
      </nav>
    </header>
  );
}
