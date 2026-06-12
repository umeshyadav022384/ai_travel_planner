const mongoose = require('mongoose');

const itinerarySchema = new mongoose.Schema({
  user: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  destination: {
    type: String,
    required: [true, 'Destination is required']
  },
  startDate: {
    type: Date,
    required: [true, 'Start date is required']
  },
  endDate: {
    type: Date,
    required: [true, 'End date is required']
  },
  travelers: {
    type: Number,
    default: 1,
    min: 1
  },
  budget: {
    type: Number,
    default: 500
  },
  preferences: {
    art: { type: Number, default: 5, min: 1, max: 10 },
    history: { type: Number, default: 5, min: 1, max: 10 },
    nature: { type: Number, default: 5, min: 1, max: 10 },
    food: { type: Number, default: 5, min: 1, max: 10 },
    adventure: { type: Number, default: 5, min: 1, max: 10 },
  },
  dailyActivities: [{
    day: Number,
    date: Date,
    activities: [{
      time: String,
      title: String,
      description: String,
      location: String,
      cost: Number,
      duration: Number
    }]
  }],
  totalCost: {
    type: Number,
    default: 0
  },
  status: {
    type: String,
    enum: ['planned', 'ongoing', 'completed', 'cancelled'],
    default: 'planned'
  }
}, {
  timestamps: true
});

module.exports = mongoose.model('Itinerary', itinerarySchema);