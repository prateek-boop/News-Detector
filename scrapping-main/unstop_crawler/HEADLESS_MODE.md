# Headless Mode Support

All scraping commands now support **headless mode** for running in the background without opening visible browser windows.

## ✅ Commands with Headless Mode

### 1. **Devpost Scraping**
```bash
# Scrape Devpost hackathons in headless mode
python manage.py scrape_devpost --from-file devpost_urls.txt --headless

# Single URL
python manage.py scrape_devpost --url https://hackthetrack.devpost.com --headless
```

### 2. **Devpost URL Collection**
```bash
# Get all Devpost URLs in headless mode
python manage.py get_devpost_urls --output devpost_urls.txt --headless

# Filter by status
python manage.py get_devpost_urls --status open --headless
```

### 3. **Unstop Hackathons** 
```bash
# Scrape Unstop hackathons in headless mode
python manage.py scrape_unstop --from-file unstop_urls.txt --headless

# Single URL
python manage.py scrape_unstop --url https://unstop.com/hackathons/... --headless
```

### 4. **Unstop Competitions**
```bash
# Scrape Unstop competitions in headless mode
python manage.py scrape_competitions --from-file competition_urls.txt --headless

# Single URL
python manage.py scrape_competitions --url https://unstop.com/competitions/... --headless
```

### 5. **Unstop URL Collection**
```bash
# Get all Unstop URLs in headless mode
python manage.py get_all_urls --output unstop_all_urls.txt --headless

# Filter hackathons only
python manage.py get_all_urls --type hackathons --headless

# Filter competitions only
python manage.py get_all_urls --type competitions --headless
```

## 🚀 Benefits of Headless Mode

1. **Faster** - No GUI rendering overhead
2. **Resource Efficient** - Lower CPU and memory usage
3. **Server Friendly** - Can run on headless servers
4. **Background** - No browser windows popping up
5. **Automation** - Perfect for cron jobs and scripts

## 💡 Usage Tips

### Recommended for Production
Always use `--headless` when running automated scraping:
```bash
python manage.py scrape_devpost --from-file devpost_urls.txt --headless
```

### For Debugging
Omit `--headless` to see what the browser is doing:
```bash
python manage.py scrape_devpost --url https://example.devpost.com
```

### Complete Workflow Example
```bash
# 1. Get all URLs (headless)
python manage.py get_devpost_urls --output devpost_urls.txt --headless

# 2. Scrape all URLs (headless)
python manage.py scrape_devpost --from-file devpost_urls.txt --headless

# 3. Export to JSON
python manage.py export_devpost --output devpost_data.json
```

## 🔧 Technical Details

- Uses Chrome's `--headless=new` flag (modern headless mode)
- Includes `--disable-gpu` and `--no-sandbox` for compatibility
- Still uses your saved browser profile for authentication
- All anti-detection features remain active

## 📝 All Commands Summary

| Command | Headless Support | Description |
|---------|-----------------|-------------|
| `scrape_unstop` | ✅ | Scrape Unstop hackathons |
| `scrape_competitions` | ✅ | Scrape Unstop competitions |
| `scrape_devpost` | ✅ | Scrape Devpost hackathons |
| `get_all_urls` | ✅ | Get all Unstop URLs |
| `get_devpost_urls` | ✅ | Get all Devpost URLs |
| `export_hackathons` | N/A | Export to JSON/CSV |
| `export_competitions` | N/A | Export to JSON/CSV |
| `export_devpost` | N/A | Export to JSON/CSV |
| `export_to_supabase` | N/A | Export to Supabase |
| `update_unstop` | ✅ | Update existing data |

