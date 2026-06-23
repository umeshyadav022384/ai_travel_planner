// server/routes/itineraryRoutes.js

const express = require('express');
const router = express.Router();

// ✅ IMPORT THE SAME WAY AS YOUR WORKING CODE
const { protected } = require('../middleware/auth');

const {
  generateItinerary,
  saveItinerary,
  getItineraries,
  getItineraryById,
  updateItineraryStatus,
  deleteItinerary,
  getSupportedDestinations
} = require('../controllers/itineraryController');

// ✅ USE THE SAME MIDDLEWARE
router.use(protected);  // All routes below require login

// Public route (no auth needed)
router.get('/supported-destinations', getSupportedDestinations);

// Protected routes
router.post('/generate', generateItinerary);
router.post('/save', saveItinerary);        // ← This will work!
router.post('/', saveItinerary);            // ← Also works
router.get('/', getItineraries);
router.get('/:id', getItineraryById);
router.put('/:id/status', updateItineraryStatus);
router.delete('/:id', deleteItinerary);

module.exports = router;