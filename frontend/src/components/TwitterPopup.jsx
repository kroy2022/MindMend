import '../Twitter.css';
import { useEffect, useState } from 'react'
import axios from 'axios';

function TwitterPopUp({ urlChange }) {
    return(
        <div className='popup-container'>
            <h1 className='enter-url-h'>Please Enter Your Twitter URL: </h1>
            <input className='input-url' placeholder='URL' onBlur={urlChange}/>
        </div>
    );
}

export default TwitterPopUp


