import Navbar from "./components/Navbar/Navbar";
import Home from "./components/Home/Home";
import Place from "./components/Place/Place";
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
         
        </Routes>
        <Footer />
      </Router>
    </>
  );
}

export default App;
