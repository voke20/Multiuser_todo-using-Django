import React, {useState} from 'react';
import AuthLayout from '../../Components/AuthLayout/AuthLayout'

const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        console.log(email, password)
    };

    return (
        // <div>
        //     <h1>Login</h1>
        //     <form onSubmit={handleSubmit}>
        //         <div>
        //             <label htmlFor="">Email</label>
        //             <input 
        //                 type="email"
        //                 value={email}
        //                 onChange={(e) => setEmail(e.target.value)}
        //                 placeholder='Enter your Email' 
        //             />
        //         </div>
        //         <div>
        //             <label htmlFor="">Password</label>
        //             <input 
        //                 type="password"
        //                 value = {password}
        //                 onChange={(e) => setPassword(e.target.value)}
        //                 placeholder='Enter your Password' />
        //         </div>
        //     </form>
        // </div>
        <AuthLayout>
            <div className="login-form-container">
                <h1>Welcome Back</h1>
                <p>Please enter your details to sign in</p>
                <div className="social-buttons">
                    <button className="btn-social">
                        <img src="https://www.google.com/favicon.ico" alt="Google" />
                        Google
                    </button>
                    <button className="btn-social">
                        <img src="" alt="" />
                        🍎 Apple
                    </button>
                </div>

                <div className="divider">
                    <span>Or EMAIL</span>
                </div>

                <form action="" onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label>Email</label>
                        <input 
                            type="email"
                            value={email}
                            onChange={(e)=> setEmail(e.target.value)}
                            placeholder='Enter your email' />
                    </div>

                    <div className="form-group">
                        <label>Password</label>
                        <input 
                            type="password"
                            value={email}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder='Enter your password' />
                    </div>

                    <div className="form-options">
                        <label>
                            <input type="checkbox" /> Remember Me
                        </label>
                        <a href="">Forgot Password</a>
                    </div>

                    <button type='submit' className="btn-primary">
                        Sign In
                    </button>
                </form>

                <p className="auth-switch">
                    Don't have an account?
                    <a href="/register">Register</a>
                </p>
            </div>
        </AuthLayout>
    );
};

export default Login;