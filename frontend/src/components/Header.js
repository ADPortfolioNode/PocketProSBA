import React from 'react';
import { Navbar, Container } from 'react-bootstrap';

function Header() {
  return (
    <Navbar bg="dark" variant="dark" expand="lg" className="mb-3">
      <Container>
        <Navbar.Brand href="/">PocketPro SBA Assistant</Navbar.Brand>
      </Container>
    </Navbar>
  );
}

export default Header;
