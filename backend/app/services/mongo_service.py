import motor.motor_asyncio
from app.core.config import settings
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from bson import ObjectId

class MongoService:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGO_DATABASE_URI)
        self.db = self.client[settings.MONGO_DATABASE_NAME]
        
        # Collections
        self.admin_logs = self.db.admin_activity_logs
        self.product_views = self.db.product_views
        self.search_history = self.db.search_history
        self.user_activities = self.db.user_activities
        self.reviews = self.db.reviews

        
    # ADMIN LOGS (Nhật ký hoạt động)
    async def push_log(self, data: Dict[str, Any]):
        if "created_at" not in data: data["created_at"] = datetime.now(timezone(timedelta(hours=7)))
        await self.admin_logs.insert_one(data)

    async def get_logs(self, filter_query: Dict = {}, skip: int = 0, limit: int = 50):
        cursor = self.admin_logs.find(filter_query).sort("created_at", -1).skip(skip).limit(limit)
        return await self._format_list(cursor, limit)

    async def delete_old_logs(self, days: int) -> int:
        cutoff = datetime.now(timezone(timedelta(hours=7))) - timedelta(days=days)
        res = await self.admin_logs.delete_many({"created_at": {"$lt": cutoff}})
        return res.deleted_count


    # ANALYTICS (Views, Search, Activity)
    # --- A. Product Views ---
    async def log_product_view(self, product_id: int, ip_address: str, user_id: Optional[int] = None):
        await self.product_views.insert_one({
            "product_id": product_id, "user_id": user_id, 
            "ip_address": ip_address, "viewed_at": datetime.now(timezone(timedelta(hours=7)))
        })

    async def get_most_viewed_products(self, days: int = 7, limit: int = 10) -> List[Dict]:
        """Thống kê top sản phẩm xem nhiều (cho Dashboard/Report)"""
        cutoff = datetime.now(timezone(timedelta(hours=7))) - timedelta(days=days)
        pipeline = [
            {"$match": {"viewed_at": {"$gte": cutoff}}},
            {"$group": {"_id": "$product_id", "view_count": {"$sum": 1}}},
            {"$sort": {"view_count": -1}},
            {"$limit": limit}
        ]
        cursor = self.product_views.aggregate(pipeline)
        results = await cursor.to_list(length=limit)
        return [{"product_id": item["_id"], "view_count": item["view_count"]} for item in results]

    async def get_recently_viewed_product_ids(self, user_id: int, limit: int = 10) -> List[int]:
        cursor = self.product_views.find({"user_id": user_id})\
                                   .sort("viewed_at", -1).limit(limit * 2)
        views = await cursor.to_list(length=limit*2)
        seen = set()
        p_ids = []
        for v in views:
            pid = v["product_id"]
            if pid not in seen:
                seen.add(pid)
                p_ids.append(pid)
            if len(p_ids) >= limit: break
        return p_ids

    # --- B. Search History ---
    async def log_search(self, keyword: str, user_id: Optional[int] = None, ip_address: str = None, results_count: int = 0):
        await self.search_history.insert_one({
            "search_query": keyword, "user_id": user_id, 
            "ip_address": ip_address, "results_count": results_count,
            "created_at": datetime.now(timezone(timedelta(hours=7)))
        })

    async def get_user_search_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        cursor = self.search_history.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
        items = await cursor.to_list(length=limit)
        return [{"search_query": i["search_query"], "results_count": i.get("results_count", 0), "searched_at": i["created_at"]} for i in items]

    async def get_popular_searches(self, days: int = 7, limit: int = 10) -> List[Dict]:
        """Thống kê từ khóa hot"""
        cutoff = datetime.now(timezone(timedelta(hours=7))) - timedelta(days=days)
        pipeline = [
            {"$match": {"created_at": {"$gte": cutoff}}},
            {"$group": {"_id": "$search_query", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        cursor = self.search_history.aggregate(pipeline)
        results = await cursor.to_list(length=limit)
        return [{"search_query": item["_id"], "search_count": item["count"]} for item in results]

    async def get_zero_result_searches(self, days: int = 7, limit: int = 50) -> List[Dict]:
        """Thống kê từ khóa không tìm thấy kết quả"""
        cutoff = datetime.now(timezone(timedelta(hours=7))) - timedelta(days=days)
        cursor = self.search_history.find({
            "created_at": {"$gte": cutoff},
            "results_count": 0
        }).sort("created_at", -1).limit(limit)
        
        items = await cursor.to_list(length=limit)
        return [{"search_query": i["search_query"], "searched_at": i["created_at"], "results_count": 0} for i in items]

    # --- C. User Activity ---
    async def log_activity(self, user_id: int, activity_type: str, metadata: Dict = None):
        await self.user_activities.insert_one({
            "user_id": user_id, "activity_type": activity_type, "metadata": metadata,
            "created_at": datetime.now(timezone(timedelta(hours=7)))
        })


    # REVIEWS
    async def create_review(self, review_data: Dict[str, Any]) -> str:
        if "created_at" not in review_data: review_data["created_at"] = datetime.now(timezone(timedelta(hours=7)))
        review_data["updated_at"] = review_data["created_at"]
        review_data["is_approved"] = False
        review_data["helpful_users"] = [] 
        result = await self.reviews.insert_one(review_data)
        return str(result.inserted_id)

    async def get_review(self, review_id: str) -> Optional[Dict]:
        if not ObjectId.is_valid(review_id): return None
        review = await self.reviews.find_one({"_id": ObjectId(review_id)})
        if review:
            review["review_id"] = str(review["_id"])
            review["helpful_count"] = len(review.get("helpful_users", []))
        return review

    async def get_reviews_by_product(self, product_id: int, skip: int = 0, limit: int = 20, rating: int = None):
        query = {"product_id": product_id, "is_approved": True}
        if rating: query["rating"] = rating
        
        cursor = self.reviews.find(query).sort("created_at", -1).skip(skip).limit(limit)
        return await self._format_list(cursor, limit)

    async def get_reviews_by_user(self, user_id: int, skip: int = 0, limit: int = 20):
        cursor = self.reviews.find({"user_id": user_id}).sort("created_at", -1).skip(skip).limit(limit)
        return await self._format_list(cursor, limit)

    async def get_pending_reviews(self, skip: int = 0, limit: int = 50):
        cursor = self.reviews.find({"is_approved": False}).sort("created_at", 1).skip(skip).limit(limit)
        return await self._format_list(cursor, limit)

    async def update_review(self, review_id: str, update_data: Dict) -> Optional[Dict]:
        if not ObjectId.is_valid(review_id): return None
        update_data["updated_at"] = datetime.now(timezone(timedelta(hours=7)))
        await self.reviews.update_one({"_id": ObjectId(review_id)}, {"$set": update_data})
        return await self.get_review(review_id)

    async def delete_review(self, review_id: str) -> bool:
        if not ObjectId.is_valid(review_id): return False
        res = await self.reviews.delete_one({"_id": ObjectId(review_id)})
        return res.deleted_count > 0

    async def approve_review(self, review_id: str, is_approved: bool) -> Optional[Dict]:
        if not ObjectId.is_valid(review_id): return None
        if is_approved:
            await self.reviews.update_one({"_id": ObjectId(review_id)}, {"$set": {"is_approved": True}})
            return await self.get_review(review_id)
        else:
            await self.reviews.delete_one({"_id": ObjectId(review_id)})
            return None

    async def toggle_helpful(self, review_id: str, user_id: int) -> int:
        if not ObjectId.is_valid(review_id): return 0
        review = await self.reviews.find_one({"_id": ObjectId(review_id)})
        if not review: return 0
        
        if user_id in review.get("helpful_users", []):
            await self.reviews.update_one({"_id": ObjectId(review_id)}, {"$pull": {"helpful_users": user_id}})
        else:
            await self.reviews.update_one({"_id": ObjectId(review_id)}, {"$addToSet": {"helpful_users": user_id}})
        
        updated = await self.reviews.find_one({"_id": ObjectId(review_id)})
        return len(updated.get("helpful_users", []))

    async def get_rating_summary(self, product_id: int) -> Dict:
        pipeline = [
            {"$match": {"product_id": product_id, "is_approved": True}},
            {"$group": {"_id": "$rating", "count": {"$sum": 1}}}
        ]
        cursor = self.reviews.aggregate(pipeline)
        results = await cursor.to_list(length=5)
        
        summary = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        total = 0
        weighted_sum = 0
        for item in results:
            r, c = item["_id"], item["count"]
            if r in summary:
                summary[r] = c
                total += c
                weighted_sum += r * c
        
        avg = (weighted_sum / total) if total > 0 else 0.0
        return {"average_rating": round(avg, 1), "total_reviews": total, "rating_distribution": summary}

    async def _format_list(self, cursor, length):
        items = await cursor.to_list(length=length)
        res = []
        for i in items:
            i["id"] = str(i["_id"])
            i["review_id"] = str(i["_id"])
            i["helpful_count"] = len(i.get("helpful_users") or [])
            res.append(i)
        return res

mongo_service = MongoService()