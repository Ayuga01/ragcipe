import Header from './Header';
import Sidebar from './Sidebar';
import './Layout.css';

export default function Layout({ children }) {
  return (
    <div className="layout">
      <Header />
      <div className="layout__body">
        <Sidebar />
        <main className="layout__main">
          <div className="layout__content">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
