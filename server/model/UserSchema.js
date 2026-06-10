const mongoose = require("mongoose");
const userSchema = new mongoose.Schema({
  name: {
    type: String,
    required: [true, "please add name"],
  },
  email: {
    type: String,
    required: [true, "please add an email"],
    unique: true,
  },
  password: {
    type: String,
    required: [true, "please add a password"],
  },
  bio:{
    type:String,
    required:[true,"please add bio"],
  },
},
{
    timestamps:true,
},
);
const User=mongoose.model("User",userSchema);
module.exports=User;
