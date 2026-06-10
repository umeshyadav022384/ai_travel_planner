const BucketList = require("../model/BucketListSchema");

const getBucketList = async (req, res) => {
    try {
        // Find all bucket list items that belong to the logged-in user
        const bucketList = await BucketList.find({ user: req.user.id });
        res.status(200).json(bucketList);
    } catch (error) {
        console.error("Error fetching bucket list:", error);
        res.status(500).json({ message: "Server Error" });
    }
};

//     Add a new item to the bucket list

const addBucketList = async (req, res) => {
    // Check if the 'place' field is provided in the request body
    if (!req.body.place) {
        return res.status(400).json({ message: "Please add a destination" });
    }

    try {
        // Create a new bucket list item in the database
        const bucketList = await BucketList.create({
            user: req.user.id,
            place: req.body.place,
        });

        res.status(201).json(bucketList); // 201 Created is more appropriate here
    } catch (error) {
        console.error("Error adding to bucket list:", error);
        res.status(500).json({ message: "Server Error" });
    }
};

// @desc    Delete an item from the bucket list
// @route   DELETE /api/bucketList/:id
const deleteBucketList = async (req, res) => {
    try {
        // Find the item by its ID to ensure it exists
        const bucketListItem = await BucketList.findById(req.params.id);

        if (!bucketListItem) {
            return res.status(404).json({ message: "No place found with this ID" });
        }

        // Check if a user is logged in
        if (!req.user) {
            return res.status(401).json({ message: "User not found" });
        }

        // Verify that the logged-in user is the owner of the bucket list item
        if (bucketListItem.user.toString() !== req.user.id) {
            return res.status(401).json({ message: "User not authorized to delete this item" });
        }

        await BucketList.findByIdAndDelete(req.params.id);

        // Return the ID of the deleted item for the frontend to use
        res.status(200).json({ id: req.params.id });

    } catch (error) {
        console.error("Error deleting bucket list item:", error);
        res.status(500).json({ message: "Server Error" });
    }
};

module.exports = { getBucketList, addBucketList, deleteBucketList };