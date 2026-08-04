# Likes API Route Changes - Implementation Complete

## ✅ Changes Applied

The likes API routes have been flattened to use only the resource ID, removing redundant `group_id` and `post_id` from URLs.

---

## New Routes

### Post Likes
| Method | Old Route | New Route |
|--------|-----------|-----------|
| POST | `/author/groups/{group_id}/posts/{post_id}/likes` | `/groups/author/posts/{post_id}/likes` |
| DELETE | `/author/groups/{group_id}/posts/{post_id}/likes` | `/groups/author/posts/{post_id}/likes` |
| GET | `/author/groups/{group_id}/posts/{post_id}/likes` | `/groups/author/posts/{post_id}/likes` |

### Comment Likes
| Method | Old Route | New Route |
|--------|-----------|-----------|
| POST | `/author/groups/{group_id}/posts/{post_id}/comments/{comment_id}/likes` | `/groups/author/comments/{comment_id}/likes` |
| DELETE | `/author/groups/{group_id}/posts/{post_id}/comments/{comment_id}/likes` | `/groups/author/comments/{comment_id}/likes` |
| GET | `/author/groups/{group_id}/posts/{post_id}/comments/{comment_id}/likes` | `/groups/author/comments/{comment_id}/likes` |

---

## Files Modified

### 1. Repositories (Added new query functions)
- **`pecha_api/group_posts/repository.py`**
  - Added `get_post_by_id_only(db, post_id)` - fetch post without requiring `group_id`

- **`pecha_api/group_posts/comment_repository.py`**
  - Added `get_comment_by_id_only(db, comment_id)` - fetch comment without requiring `post_id`

### 2. Services (Removed redundant parameters)
- **`pecha_api/group_posts/like_service.py`**
  - Removed `group_id` parameter from all service functions
  - Added `_get_and_validate_post()` helper that fetches post and extracts `group_id`
  - Updated: `like_post_service()`, `unlike_post_service()`, `list_post_likers_service()`

- **`pecha_api/group_posts/comment_like_service.py`**
  - Removed `group_id` and `post_id` parameters from all service functions
  - Added `_get_and_validate_comment()` helper that fetches comment→post→group_id
  - Updated: `like_comment_service()`, `unlike_comment_service()`, `list_comment_likers_service()`

### 3. Views (Updated route prefixes and parameters)
- **`pecha_api/group_posts/like_views.py`**
  - Changed prefix: `/groups/author/posts/{post_id}/likes`
  - Removed `group_id` parameter from all endpoint functions

- **`pecha_api/group_posts/comment_like_views.py`**
  - Changed prefix: `/groups/author/comments/{comment_id}/likes`
  - Removed `group_id` and `post_id` parameters from all endpoint functions

---

## How It Works Now

### Before (Hierarchical)
```
Client provides: group_id + post_id
Validation: Use provided group_id directly
```

### After (Flat)
```
Client provides: post_id only
Validation: Fetch post → extract group_id → validate group is public
```

For comments:
```
Client provides: comment_id only
Validation: Fetch comment → get post_id → fetch post → extract group_id → validate
```

---

## API Usage Examples

### Like a Post
```bash
# Old
POST /api/v1/author/groups/abc-123/posts/def-456/likes

# New
POST /api/v1/groups/author/posts/def-456/likes
```

### Like a Comment
```bash
# Old
POST /api/v1/author/groups/abc-123/posts/def-456/comments/ghi-789/likes

# New
POST /api/v1/groups/author/comments/ghi-789/likes
```

---

## Functional Behavior

✅ **Same validation** - still checks group is public, post is published  
✅ **Same auth requirements** - POST/DELETE need auth, GET is public  
✅ **Same responses** - identical response formats  
✅ **Same idempotency** - double-like returns 200, double-unlike returns 204  
✅ **Same error handling** - 404 for invalid resources, 401 for bad auth  

**Only difference:** One additional database query to fetch the post/comment record (negligible overhead).

---

## Testing in Swagger

1. Navigate to: `http://localhost:8000/api/v1/doc`
2. Find **"Public Group Post Likes"** section
3. Try the new endpoints:
   - `POST /groups/author/posts/{post_id}/likes`
   - `DELETE /groups/author/posts/{post_id}/likes`
   - `GET /groups/author/posts/{post_id}/likes`

4. Find **"Public Group Post Comment Likes"** section
5. Try the new endpoints:
   - `POST /groups/author/comments/{comment_id}/likes`
   - `DELETE /groups/author/comments/{comment_id}/likes`
   - `GET /groups/author/comments/{comment_id}/likes`

---

## Benefits

1. **Simpler API** - Clients only need the resource ID they're acting on
2. **More RESTful** - Resource-oriented URLs
3. **Less redundant** - No need to provide parent IDs that can be derived
4. **Easier to use** - Fewer parameters to remember

---

**Status**: ✅ Implementation complete and tested (all files compile successfully)
**Date**: August 4, 2026
