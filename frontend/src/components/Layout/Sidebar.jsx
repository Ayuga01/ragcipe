import { NavLink, useLocation } from 'react-router-dom';
import { Home, Camera, BookOpen, Upload } from 'lucide-react';
import './Sidebar.css';

import { Bookmark } from 'lucide-react';

const navItems = [
  { path: '/', icon: Home, label: 'Home' },
  { path: '/scan', icon: Camera, label: 'Scan' },
  { path: '/recipes', icon: BookOpen, label: 'Recipes' },
  { path: '/saved', icon: Bookmark, label: 'Favorites' },
];

if (import.meta.env.DEV || import.meta.env.VITE_ENABLE_ADMIN === 'true') {
  navItems.push({ path: '/library', icon: Upload, label: 'Library' });
}

export default function Sidebar() {
  const location = useLocation();

  return (
    <>
      {/* Desktop Sidebar */}
      <aside className="sidebar hide-mobile">
        <nav className="sidebar__nav">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={`sidebar__link ${isActive ? 'sidebar__link--active' : ''}`}
              >
                <div className="sidebar__icon-wrap">
                  <Icon size={20} />
                  {isActive && <div className="sidebar__glow" />}
                </div>
                <span className="sidebar__label">{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
      </aside>

      {/* Mobile Bottom Nav */}
      <nav className="bottom-nav show-mobile">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={`bottom-nav__link ${isActive ? 'bottom-nav__link--active' : ''}`}
            >
              <Icon size={20} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>
    </>
  );
}
