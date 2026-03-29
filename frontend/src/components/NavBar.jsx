import { NavLink } from 'react-router-dom';

export default function NavBar() {
  return (
    <header className="topbar">
      <div>
        <p className="eyebrow">Agentic GenAI prototype</p>
        <h1>Contract AI Assistant</h1>
      </div>
      <nav className="topbar-nav">
        <NavLink to="/" end className={({ isActive }) => `nav-pill ${isActive ? 'is-active' : ''}`}>
          Workspace
        </NavLink>
        <NavLink to="/help" className={({ isActive }) => `nav-pill ${isActive ? 'is-active' : ''}`}>
          Help / Presentation map
        </NavLink>
      </nav>
    </header>
  );
}
