import { useEffect, useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import axios from 'axios';
import {Navbar, NavbarBrand, NavbarContent, NavbarItem, Link, Button} from "@nextui-org/react";
import { useNavigate } from 'react-router-dom';
import pic from './assets/mental-health.png';

function App() {
  const [count, setCount] = useState(0);
  const navigate = useNavigate();

  useEffect(() => {
    const fd = new FormData();
    fd.append("link", "test");
    axios.post('http://127.0.0.1:5000/twitter/info', fd, {
      headers: {
          'Content-Type': 'multipart/form-data',
      }
    })
    .then(response => console.log(response))
    .catch(error => console.log(error))
  }, [])

  const handleLoginNavigation = () => {
    navigate("/Login", {state: null});
  }

  return (
    <div className='landing-container'>
      {/* <Navbar >
        <NavbarBrand>
          <p className="font-bold text-inherit">ACME</p>
        </NavbarBrand>
        <NavbarContent className="hidden sm:flex gap-4" justify="center">
          <NavbarItem>
            <Link color="foreground" href="#">
              Features
            </Link>
          </NavbarItem>
          <NavbarItem isActive>
            <Link href="#" aria-current="page">
              Customers
            </Link>
          </NavbarItem>
          <NavbarItem>
            <Link color="foreground" href="#">
              Integrations
            </Link>
          </NavbarItem>
        </NavbarContent>
        <NavbarContent justify="end">
          <NavbarItem className="hidden lg:flex">
            <Link href="#">Login</Link>
          </NavbarItem>
          <NavbarItem>
            <Button as={Link} color="primary" href="#" variant="flat">
              Sign Up
            </Button>
          </NavbarItem>
        </NavbarContent>
      </Navbar> */}
      <div className='start-content'>
        <div className='content'>
          <div className='start-headers'>
            <h1 className='start-header'>Next <span className='highlight'>Generation</span> Mental Health Tool.</h1>
            <p className='start-p'>Empower your circle. Share your thoughts, feelings, and progress, and let us amplify your mental well-being - powered by AI.</p>
          </div>
          <div className='start-svg'>
            <img className="startpage-svg" src ={pic} alt="saving-book"/>
          </div>
        </div>
        <button onClick={handleLoginNavigation} className='land-login-btn'>Get Started</button>
        <div className='bottom-fade'></div>
      </div>
    </div>
  )
}

export default App


