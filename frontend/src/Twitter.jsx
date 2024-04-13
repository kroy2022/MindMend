import './Twitter.css';
import { useEffect, useState } from 'react'
import axios from 'axios';
import Popup from './components/TwitterPopup.jsx';

function Twitter() {
    const [load, setLoad] = useState(true);
    const [url, setUrl] = useState('');
    const [users, setUsers] = useState([]);
    const [loadingUsers, setLoadingUsers] = useState(true);
    const [currentNumber, setCurrentNumber] = useState(0);
    const handleUrl = (event) => {
        console.log("URL: ", event.target.value);
        setUrl(event.target.value);
        let temp = []
        temp.push({
            "name": "Kevin Roy",
            "tweet_id": 1,
            "tweet": "I hate my life",
            "rank": .75,
        })
        temp.push({
            "name": "Emma Roy",
            "tweet_id": 2,
            "tweet": "I would kill for a soda right now",
            "rank": .2,
        })
        temp.push({
            "name": "Drew Meyer",
            "tweet_id": 3,
            "tweet": "I want to die",
            "rank": .85,
        })
        temp.push({
            "name": "Idk",
            "tweet_id": 1,
            "tweet": "I hate my life",
            "rank": .75,
        })
        temp.push({
            "name": "Idk 2",
            "tweet_id": 2,
            "tweet": "I would kill for a soda right now",
            "rank": .2,
        })
        temp.push({
            "name": "Idk 3",
            "tweet_id": 3,
            "tweet": "I want to die",
            "rank": .85,
        })
        temp.push({
            "name": "Idk4",
            "tweet_id": 1,
            "tweet": "I hate my life",
            "rank": .75,
        })
        temp.push({
            "name": "Idk 5",
            "tweet_id": 2,
            "tweet": "I would kill for a soda right now",
            "rank": .2,
        })
        temp.push({
            "name": "Idk 6",
            "tweet_id": 3,
            "tweet": "I want to die",
            "rank": .85,
        })
        setUsers(temp);
        handleResponse(temp);
        setLoad(false);
    }

    const handleResponse = (response) => {
        setLoadingUsers(false);
    }

    const displayUser = (index) => {
        setCurrentNumber(index);
    }

    return (
        <div className='twitter-container'>
            {load && <Popup urlChange={handleUrl}/>}
            {loadingUsers ? (
                <div className='loading-container'>
                    Loading...
                </div>
            ) :(
                <div className='display-info'>
                    <div className='specific-user'>
                        <h2>{users[currentNumber]["name"]} recieved a {users[currentNumber]["rank"]} ranking</h2>
                        <p>The following tweet was marked as an indiciation of this: </p>
                        <h1>Tweet: {users[currentNumber]["tweet"]}</h1>
                        <h1>Tweet ID: {users[currentNumber]["tweet_id"]}</h1>
                        <button className='find-resources-btn'>How can I help?</button>
                    </div>
                    <div className='all-users'>
                        <h1>Select a user</h1>
                        <div className='users'>
                            {users.map((user, index) => (
                                <div className='user-div' onClick={() => displayUser(index)}>
                                    <h1 className='user-name'>{user.name}</h1>
                                    <h1 className='rank'>{user.rank}</h1>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default Twitter