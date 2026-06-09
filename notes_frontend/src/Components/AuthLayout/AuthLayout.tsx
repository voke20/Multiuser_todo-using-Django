import React from 'react';
import './AuthLayout.css'

interface AuthLayoutProps {
    children: React.ReactNode;
}

const AuthLayout = ({children} : AuthLayoutProps ) => {
    return (
        <div className="auth-container">
            {/* left panel */}
            <div className="auth-left">
                <div className="auth-logo">
                    <span>📑</span>
                    <h2>Notes App</h2>
                </div>
                <h1>Elevate your thoughts to new heights</h1>
                <p>
                    The digital santuary for knowledge workers. Organize, synthesize in a space 
                    designed for focus and intellectual sophistication.
                </p>
            </div>
            {/* right panel */}
            <div className="auth-right">
                {children}
            </div>
        </div>
    );
};

export default AuthLayout;