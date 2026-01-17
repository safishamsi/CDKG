# 🧪 Testing Production with Updated Knowledge Graph

## Step 1: Start Backend

```bash
cd /Users/safi/Downloads/cdkg-challenge-main
python3.9 backend_api_youtube.py
```

**Keep this terminal open** - backend needs to keep running.

---

## Step 2: Run Migration (If Needed)

If you have existing Tag nodes in Neo4j, migrate them first:

```bash
# In a new terminal
cd /Users/safi/Downloads/cdkg-challenge-main
python3.9 migrate_tags_to_properties.py
```

This will:
- Convert Tag nodes to `Talk.tags` property
- Delete Tag nodes and relationships
- Update all Talk nodes

---

## Step 3: Run Production Tests

```bash
# In a new terminal
cd /Users/safi/Downloads/cdkg-challenge-main
python3.9 test_production.py
```

**Expected Results:**
- ✅ Health check passes
- ✅ Graph data excludes Tag nodes
- ✅ Talk nodes have `tags` property
- ✅ Query endpoint works
- ✅ Stats show no Tag nodes

---

## Step 4: Test Frontend

1. **Start frontend** (if testing locally):
   ```bash
   cd frontend
   npm run dev
   ```

2. **Or use deployed frontend**:
   - Go to your Vercel URL
   - Open Knowledge Graph visualization
   - Verify:
     - ✅ No Tag nodes visible
     - ✅ Talk nodes show tags in properties panel
     - ✅ Organization nodes visible (if they exist)

---

## Step 5: Test with New YouTube Video

Process a new YouTube video to verify tags are stored as property:

```bash
# Test YouTube processing
python3.9 -c "
from youtube_processor import YouTubeVideoProcessor
processor = YouTubeVideoProcessor()
# Process a test video URL
result = processor.process_video('https://www.youtube.com/watch?v=YOUR_VIDEO_ID')
print('Tags stored as property:', result.get('tags_stored_as_property', False))
"
```

---

## ✅ Verification Checklist

- [ ] Backend running and healthy
- [ ] Migration completed (if needed)
- [ ] Graph data excludes Tag nodes
- [ ] Talk nodes have `tags` property
- [ ] Frontend graph visualization works
- [ ] No Tag nodes in visualization
- [ ] Organization nodes visible (if exist)
- [ ] Query endpoint returns correct results

---

## 🐛 Troubleshooting

### Backend Won't Start
- Check Neo4j is running
- Verify `.env` file has correct credentials
- Check port 8000 is not in use

### Migration Fails
- Verify Neo4j connection
- Check `.env` file has `NEO4J_PASSWORD`
- Ensure Neo4j Desktop is running

### Tag Nodes Still Appear
- Run migration script again
- Check graph query excludes Tag nodes
- Verify frontend filters Tag nodes

### Frontend Can't Connect
- Check `VITE_API_URL` is set correctly
- Verify backend is running
- Check CORS settings

---

## 📊 Expected Graph Structure

**Before (Old):**
```
(:Talk)-[:IS_DESCRIBED_BY]->(:Tag)
```

**After (New):**
```
(:Talk {tags: ["tag1", "tag2", ...]})
```

**Node Types (After Fix):**
- ✅ Speaker
- ✅ Talk (with tags property)
- ✅ Event
- ✅ Category
- ✅ Organization
- ✅ Product
- ✅ Concept
- ✅ Community
- ❌ Tag (removed)

---

## 🚀 Next Steps

1. **Deploy to Production**:
   - Backend: Railway/Render
   - Frontend: Vercel (already deployed)

2. **Update Environment Variables**:
   - Set `VITE_API_URL` to production backend URL

3. **Monitor**:
   - Check logs for errors
   - Verify graph visualization
   - Test query functionality

---

**Ready to test!** Follow the steps above to verify everything works with the updated knowledge graph structure.

