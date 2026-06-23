const router = require("express").Router();
const { chatReply } = require("../controllers/chatbot");

router.post("/", chatReply);

module.exports = router;
