# DebuTube Deployment Guide 🚀

This guide will help you deploy DebuTube to Vercel successfully.

## Prerequisites

- Node.js 18+ installed locally
- Python 3.7+ installed locally  
- Vercel account (free tier works)
- Git repository

## Local Testing

Before deploying, test the application locally:

1. **Install dependencies:**
   ```bash
   npm install
   pip install yt-dlp
   ```

2. **Test yt-dlp functionality:**
   ```bash
   python test-local.py
   ```

3. **Run development server:**
   ```bash
   npm run dev
   ```

4. **Open browser:** Navigate to `http://localhost:3000`

## Vercel Deployment

### Method 1: Vercel Dashboard (Recommended)

1. **Fork this repository** to your GitHub account

2. **Connect to Vercel:**
   - Go to [vercel.com](https://vercel.com)
   - Sign in with GitHub
   - Click "New Project"
   - Import your forked repository

3. **Configure deployment:**
   - Framework Preset: `Next.js`
   - Root Directory: `./` (leave default)
   - Build and Output Settings: Use defaults
   - Environment Variables: None needed

4. **Deploy:** Click "Deploy" button

### Method 2: Vercel CLI

1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel:**
   ```bash
   vercel login
   ```

3. **Deploy:**
   ```bash
   vercel --prod
   ```

## Configuration Files

The project includes these configuration files for Vercel:

- `vercel.json` - Vercel deployment configuration
- `requirements.txt` - Python dependencies
- `package.json` - Node.js dependencies
- `next.config.js` - Next.js configuration

## API Endpoints

After deployment, your app will have these endpoints:

- `GET /` - Main application interface
- `POST /api/formats` - Fetch YouTube video formats
- `POST /api/direct-url` - Get direct download URL

## Important Notes

### Vercel Limitations

- **Function timeout:** 10 seconds on free tier, 60s on pro
- **Memory limit:** 1024MB function memory
- **Execution time:** Some large videos may timeout

### YouTube Limitations

- **Rate limiting:** YouTube may rate limit requests
- **Link expiration:** Direct URLs expire in few hours
- **Region restrictions:** Some videos may not be available

### Legal Considerations

- Respect YouTube's Terms of Service
- Only download content you have rights to
- Consider copyright laws in your jurisdiction

## Troubleshooting

### Common Issues

1. **yt-dlp not found:**
   - Ensure `requirements.txt` includes `yt-dlp`
   - Check Vercel build logs

2. **Function timeout:**
   - Try with shorter videos
   - Consider upgrading to Vercel Pro

3. **CORS errors:**
   - Check API function headers
   - Ensure proper request format

4. **Build failures:**
   - Check Node.js version compatibility
   - Verify all dependencies are listed

### Debug Steps

1. **Check Vercel Function Logs:**
   - Go to Vercel Dashboard
   - Select your project
   - View "Functions" tab
   - Check logs for errors

2. **Test API endpoints manually:**
   ```bash
   curl -X POST https://your-app.vercel.app/api/formats \
     -H "Content-Type: application/json" \
     -d '{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
   ```

3. **Local testing:**
   ```bash
   python test-local.py
   npm run dev
   ```

## Performance Optimization

1. **Caching:** Consider implementing request caching
2. **Error handling:** Robust error handling is included
3. **Timeout handling:** 30-second timeout on yt-dlp commands
4. **Input validation:** YouTube URL validation included

## Security

- No API keys required
- No user data stored
- CORS properly configured
- Input validation implemented

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review Vercel deployment logs
3. Test locally with `python test-local.py`
4. Ensure all dependencies are correctly listed

## Updates

To update your deployment:

1. Push changes to your GitHub repository
2. Vercel will automatically redeploy
3. Or use `vercel --prod` for manual deployment

---

**Happy deploying! 🎉** 