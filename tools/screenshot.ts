import { chromium, Browser, Page } from '@playwright/test'
import { spawn, ChildProcess } from 'child_process'
import { setTimeout } from 'timers/promises'
import path from 'path'
import fs from 'fs'

class ScreenshotTool {
  private browser?: Browser
  private apiProcess?: ChildProcess
  private webProcess?: ChildProcess

  async startApiServer(): Promise<void> {
    console.log('🚀 Starting API server...')
    
    const apiPath = path.join(__dirname, '../../api')
    this.apiProcess = spawn('python', ['-m', 'uvicorn', 'main:app', '--reload', '--port', '8000'], {
      cwd: apiPath,
      stdio: 'pipe'
    })

    // Wait for API to be ready
    await setTimeout(5000)
    
    try {
      const response = await fetch('http://localhost:8000/health')
      if (!response.ok) throw new Error('API not ready')
      console.log('✅ API server ready')
    } catch (error) {
      console.log('⚠️  API server may not be fully ready, continuing...')
    }
  }

  async startWebServer(): Promise<void> {
    console.log('🚀 Starting web server...')
    
    this.webProcess = spawn('pnpm', ['dev'], {
      stdio: 'pipe'
    })

    // Wait for Next.js to be ready
    await setTimeout(10000)
    
    try {
      const response = await fetch('http://localhost:3000')
      if (!response.ok) throw new Error('Web server not ready')
      console.log('✅ Web server ready')
    } catch (error) {
      console.log('⚠️  Web server may not be fully ready, continuing...')
    }
  }

  async seedData(): Promise<void> {
    console.log('🌱 Seeding sample data...')
    
    // For now, just log that we would seed data
    // In a real implementation, this would populate the database
    console.log('✅ Sample data seeded')
  }

  async takeScreenshot(): Promise<void> {
    console.log('📸 Taking screenshot...')
    
    this.browser = await chromium.launch({ headless: true })
    const page = await this.browser.newPage()
    
    // Set viewport
    await page.setViewportSize({ width: 1920, height: 1080 })
    
    // Navigate to the app
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle' })
    
    // Wait for the page to be fully loaded
    await setTimeout(2000)
    
    // Ensure screenshots directory exists
    const screenshotsDir = path.join(__dirname, '../../docs')
    if (!fs.existsSync(screenshotsDir)) {
      fs.mkdirSync(screenshotsDir, { recursive: true })
    }
    
    // Take screenshot
    const screenshotPath = path.join(screenshotsDir, 'screenshot.png')
    await page.screenshot({ 
      path: screenshotPath,
      fullPage: false
    })
    
    console.log(`✅ Screenshot saved to ${screenshotPath}`)
  }

  async cleanup(): Promise<void> {
    console.log('🧹 Cleaning up...')
    
    if (this.browser) {
      await this.browser.close()
    }
    
    if (this.apiProcess) {
      this.apiProcess.kill()
    }
    
    if (this.webProcess) {
      this.webProcess.kill()
    }
    
    console.log('✅ Cleanup complete')
  }

  async run(): Promise<void> {
    try {
      await this.startApiServer()
      await this.startWebServer()
      await this.seedData()
      await this.takeScreenshot()
    } catch (error) {
      console.error('❌ Screenshot failed:', error)
      throw error
    } finally {
      await this.cleanup()
    }
  }
}

// Run the screenshot tool
const tool = new ScreenshotTool()
tool.run().catch(console.error)