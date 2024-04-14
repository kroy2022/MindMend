import './Twitter.css';
import { useEffect, useState } from 'react'
import axios from 'axios';
import Popup from './components/TwitterPopup.jsx';
import MessagePopup from './components/MessagePopup.jsx';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faFaceSadTear } from '@fortawesome/free-solid-svg-icons'; 
import { faFaceMeh } from '@fortawesome/free-solid-svg-icons'; 
import { faFaceSmile } from '@fortawesome/free-solid-svg-icons'; 
import { TwitterTweetEmbed } from 'react-twitter-embed';
import { useLocation } from "react-router-dom";

function Twitter() {   
    //https://twitter.com/JohnDoe1469136
    const location = useLocation();
    const data = location.state;
    const [load, setLoad] = useState(true);
    const [url, setUrl] = useState('');
    const [users, setUsers] = useState([]);
    const [loadingUsers, setLoadingUsers] = useState(true);
    const [currentNumber, setCurrentNumber] = useState(0);
    const [resources, setResources] = useState([]);
    const [email, setEmail] = useState('');
    const [loadEmergency, setLoadEmergency] = useState(false);
    const [message, setMessage] = useState("");
    const [tweetId, setTweetId] = useState(0);

    const phoneNumbers = [
        {
            "name": "National Suicide Prevention Lifeline",
            "number": "800-273-8255 (TALK)"
        },
        {
            "name": "SAMHSA (Substance Abuse and Mental Health Services Administration)",
            "number": "800-662-435 (HELP)"
        },
        {
            "name": "Samaritans",
            "number": "877-870-4673 (HOPE)"
        },
        {
            "name": "Friendship Line",
            "number": "800-971-0016"
        }
    ]

    useEffect(() => {
        setEmail(data);
    }, [])

    const handleUrl = (event) => {
        const fd = new FormData();
        fd.append("link", event.target.value);
        axios.post('http://127.0.0.1:5000/twitter/info', fd, {
        headers: {
            'Content-Type': 'multipart/form-data',
        }
        })
        .then(response => handleResponse(response))
        .catch(error => console.log(error))
        setLoad(false);
    }

    const handleResponse = (response) => {
        console.log(response);
        let tempUsers = []
        tempUsers = response.data.users;
        for(let i = 0; i < tempUsers.length; i++){
            tempUsers[i].tweet = tempUsers[i].tweet.replace(/\d/g, '');
        }
        setTweetId(tempUsers[0]["id"]);
        console.log(tweetId);
        setUsers(tempUsers);
        setLoadingUsers(false);
    }

    const displayUser = (index) => {
        console.log("users: ", users);
        console.log("Tweet ID: ", tweetId);
        setCurrentNumber(index);
        setTweetId(users[currentNumber]["id"]);
    }

    const findResources = () => {
        const fd = new FormData();
        fd.append("tweet", users[currentNumber]["tweet"]);
        axios.post('http://127.0.0.1:5000/get/resources', fd, {
        headers: {
            'Content-Type': 'multipart/form-data',
        }
        })
        .then(response => handleLinks(response))
        .catch(error => console.log(error))
    }

    const handleLinks = (response) => {
        console.log(response);
        setMessage("Here are some resources to help approach this situation")
        setResources(response.data.results);
    }

    const handleResources = () => {
        setResources([]);
    }

    const loadEmail = () => {
        const subject = encodeURIComponent("Urgent Help Required");
        const body = encodeURIComponent(`Hello,\n\nI have a friend who is currently suffering from mental health problems. I'm not sure how to approach them and help them out. I am concerned because of this tweet they put out:\n\n${users[currentNumber]["tweet"]}\n\nAny help would be appreciated.`);
        
        const mailtoUrl = `mailto:jo@samaritans.org?subject=${subject}&body=${body}`;
        window.location.href = mailtoUrl;
    }

    const handleEmergency = () => {
        console.log("emergency");
        setMessage("Contact These Numbers for Free Help: ")
        setLoadEmergency(!loadEmergency);
        console.log(loadEmergency);
    }

    return (
        <div className='twitter-container'>
            {resources.length > 0 && <MessagePopup message={message} onClose={handleResources} contacts={resources} type="resources" />}
            {loadEmergency && <MessagePopup message={message} onClose={handleEmergency} contacts={phoneNumbers} type="numbers" />}
            {load && <Popup urlChange={handleUrl}/>}
            {loadingUsers ? (
                <div className='loading-container'>
                    Loading...
                </div>
            ) :(
                <div className='display-info'>
                    <div className='specific-user'>
                        <h2 className='user-name-h'>{users[currentNumber]["real_name"]} recieved a {users[currentNumber]["sentiment"]} ranking</h2>
                        <div className='emjoi-display'>
                            {users[currentNumber].sentiment === 'positive' && (
                                <FontAwesomeIcon icon={faFaceSmile} className='emoji-positive'/>
                            )}
                            {users[currentNumber].sentiment === 'neutral' && (
                                <FontAwesomeIcon icon={faFaceMeh} className='emoji-neutral'/>
                            )}
                            {users[currentNumber].sentiment === 'negative' && (
                                <FontAwesomeIcon icon={faFaceSadTear} className='emoji-sad'/>
                            )}
                        </div>
                        <p>The following tweet was marked as an indiciation of this: </p>
                        <TwitterTweetEmbed key={users[currentNumber]["id"]} tweetId={users[currentNumber]["id"]} width={500} />
                        <div className='help-btns'>
                            <button className='find-resources-btn-h' onClick={findResources}>How can I help?</button>
                            <button className='find-resources-btn-r' onClick={loadEmail}>Get Advice</button>
                            <button className='find-resources-btn-b' onClick={handleEmergency}>Emergency Contact</button>
                        </div>
                    </div>
                    <div className='all-users'>
                        <h1>Select a user</h1>
                        <div className='users'>
                            {users.map((user, index) => ( 
                                <div className='user-div' onClick={() => displayUser(index)}>
                                    <h1 className='user-name'>{user.real_name}</h1>
                                    <h1 className='rank'>{user.sentiment}</h1>
                                    {user.sentiment === 'positive' && (
                                        <FontAwesomeIcon icon={faFaceSmile} className='emoji-positive'/>
                                    )}
                                    {user.sentiment === 'neutral' && (
                                        <FontAwesomeIcon icon={faFaceMeh} className='emoji-neutral'/>
                                    )}
                                    {user.sentiment === 'negative' && (
                                        <FontAwesomeIcon icon={faFaceSadTear} className='emoji-sad'/>
                                    )}
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