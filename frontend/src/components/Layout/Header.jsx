import { Link, useLocation } from 'react-router-dom';
import { ChefHat, Sparkles } from 'lucide-react';
import './Header.css';

const navLinks = [
  { path: '/', label: 'Home' },
  { path: '/scan', label: 'Scan' },
  { path: '/recipes', label: 'Recipes' },
  { path: '/library', label: 'Library' },
];

export default function Header() {
  const location = useLocation();

  return (
    <header className="header">
      <div className="header__inner">
        <Link to="/" className="header__brand">
          <div className="header__logo">
            <ChefHat size={28} />
            <Sparkles size={14} className="header__sparkle" />
          </div>
          <div className="header__text">
            <h1 className="header__title">
              Rag<span className="gradient-text">cipe</span>
            </h1>
            <span className="header__subtitle">Smart Recipe Generator</span>
          </div>
        </Link>

        <nav className="header__nav hide-mobile">
          {navLinks.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              className={`header__nav-link ${
                location.pathname === link.path ? 'header__nav-link--active' : ''
              }`}
            >
              {link.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
