import { useEffect, useState } from 'react'
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import './Login.css';
import pic from './assets/aboutus.svg';

function Login() {
    const navigate = useNavigate();
    const [email, setEmail] = useState('');

    const navigateToDashboard = () => {
        navigate("/Twitter",  {state: email});
    }

    const handleEmail = (event) => {
        setEmail(event.target.value);
    }

    return (
        <div className='login-container'>
            <div className='login-section'>
                <h2 className='welc-h'>Welcome Back!</h2>
                <div className='username-section'>
                    <p>Username:</p>
                    <input className='username' placeholder='Username' onChange={handleEmail}/>
                </div>
                <div className='password-section'>
                    <p>Password:</p>
                    <input type="password" className='password' placeholder='Password' />
                </div>
                <button className='login-btn' onClick={navigateToDashboard}>Login</button>
            </div>
            <div className='design-section'>
                <img src={pic} className='login-img' alt="cant load" />
                <h1 className='title'>MindMend</h1>
            </div>
        </div>
    )
}

export default Login