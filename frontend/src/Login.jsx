import { useEffect, useState } from 'react'
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import './Login.css';

function Login() {
    const navigate = useNavigate();

    const navigateToDashboard = () => {
        navigate("/Twitter",  {state: null});
    }
    return (
        <div className='login-container'>
            <div className='login-section'>
                <h2>Welcome Back!</h2>
                <div className='username-section'>
                    <p>Username:</p>
                    <input className='username' placeholder='Username' />
                </div>
                <div className='password-section'>
                    <p>Password:</p>
                    <input type="password" className='password' placeholder='Password' />
                </div>
                <button className='login-btn' onClick={navigateToDashboard}>Login</button>
            </div>
            <div className='design-section'>
                <img src="https://www.figma.com/file/ScpBXWFv1MNVBqBmsYiNuo/login_page-(Community)?type=design&node-id=2-7&mode=design&t=h55KNNywCnP5mamN-4" className='login-img' alt="cant load" />
            </div>
        </div>
    )
}

export default Login