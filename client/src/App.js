import Navbar from "./components/Navbar/Navbar";
import Home from "./components/Home/Home";
import Place from "./components/Place/Place";
import Login from "./components/Login/Login"
import Register from "./components/Register/Register";
import Profile from "./components/Profile/Profile";
import Chatbot from "./components/Chatbot/Chatbot";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Footer from "./components/Footer/Footer";

function App() {
  return (
    <>
      <Router>
        <Navbar />
        <Routes>
          <Route path="/" element={<Home />} />
           <Route path="/place" element={<Place />} />
          <Route path="/chatbot" element={<Chatbot />} />
         <Route path ="/login" element={<Login/>}/>
         <Route path="/profile" element={<Profile />} />
         <Route path="/register" element={<Register />} />
        </Routes>
        <Footer />
      </Router>
    </>
  );
}

export default App;
