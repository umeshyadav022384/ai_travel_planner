const express = require('express');
const router = express.Router();
const { protected } = require('../middleware/auth');
const {
  generateItinerary,
  saveItinerary,
  getItineraries,
  getItineraryById,
  updateItineraryStatus,
  deleteItinerary
} = require('../controllers/itineraryController');

router.use(protected);  // All routes below require login

// Generate itinerary (does NOT save to DB)
router.post('/generate', generateItinerary);

// Save itinerary to database
router.post('/', saveItinerary);

// Get all user itineraries
router.get('/', getItineraries);

// Get single itinerary by ID
router.get('/:id', getItineraryById);

// Update itinerary status
router.put('/:id/status', updateItineraryStatus);

// Delete itinerary
router.delete('/:id', deleteItinerary);

module.exports = router;