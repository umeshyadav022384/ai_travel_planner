const express = require("express");
const path = require("path");
const cors = require("cors");
//const { spawn } = require("child_process");

const authRoutes = require("./routes/auth");
const userRoutes = require("./routes/user");
const bucketListRoutes = require("./routes/bucketList");
const dotenv=require('dotenv');
const connectDB=require('./config/db')
dotenv.config();
connectDB();
const app=express();
const PORT=process.env.PORT || 5001;
app.use(cors());
app.use(express.json());
app.use("/api/auth", authRoutes);
app.use("/api/bucketList", bucketListRoutes);

app.get('/api/health',(req,res)=>{
    res.json({status:"ok"})
});
app.listen(PORT,()=>{
    console.log(`server is running on port ${PORT}`)
})