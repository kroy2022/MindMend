import '../Twitter.css';

function MessagePopup({ message, onClose, contacts, type }){

    if(type == "numbers"){
        return (
            <div className='popup-container'>
                <h1 className='enter-url-h'>{message}</h1>
                {contacts.map((contact, index) => (
                    <div className="contact" key={index}>
                        <h3 className="contact-name">{contact.name}: </h3>
                        <h3 className="contact-number">{contact.number}</h3>
                    </div>
                ))}
                <button className="close-popup" onClick={onClose}>Close</button>
            </div>
        )
    }
    return (
        <div className='popup-container'>
            <h1 className='enter-url-h'>{message}</h1>
            {contacts.map((contact, index) => (
                <div className="contact" key={index}>
                   <a className='contact-link' href="url">{contact}</a>
                </div>
            ))}
            <button className="close-popup" onClick={onClose}>Close</button>
        </div>
    )
}

export default MessagePopup