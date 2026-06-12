const express = require("express");
const path = require("path");
const cors = require("cors");
//const { spawn } = require("child_process");
require("dotenv").config();
const authRoutes = require("./routes/auth");
const bucketListRoutes = require("./routes/bucketList");
const itineraryRoutes=require("./routes/itineraryRoutes")

const connectDB = require("./config/db");

connectDB();

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

app.use("/api/auth", authRoutes);
app.use("/api/bucketList", bucketListRoutes);

app.use('/api/itineraries', itineraryRoutes);

app.get('/api/health',(req,res)=>{
    res.json({status:"ok"})
});
app.listen(PORT,()=>{
    console.log(`server is running on port ${PORT}`)
})