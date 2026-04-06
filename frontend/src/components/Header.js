import React from 'react';
import { Navbar, Container } from 'react-bootstrap';

function Header() {
  return (
    <Navbar expand="lg" className="mb-3 app-header">
      <Container>
        <Navbar.Brand href="/">PocketPro SBA Assistant</Navbar.Brand>
      </Container>
    </Navbar>
  );
}

export default Header;
