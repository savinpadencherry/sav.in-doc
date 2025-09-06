import Image from 'next/image'
import { Truck, MapPin, Clock, DollarSign } from 'lucide-react'

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700 bg-slate-900/50 backdrop-blur">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <Truck className="h-5 w-5 text-white" />
            </div>
            <h1 className="text-xl font-bold text-white">ChainSync</h1>
          </div>
          <nav className="hidden md:flex space-x-6">
            <a href="/" className="text-blue-400 hover:text-blue-300">Dashboard</a>
            <a href="/orders" className="text-slate-300 hover:text-white">Orders</a>
            <a href="/planner" className="text-slate-300 hover:text-white">Planner</a>
            <a href="/routes" className="text-slate-300 hover:text-white">Routes</a>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">Distance Saved</p>
                <p className="text-2xl font-bold text-white">127 mi</p>
              </div>
              <MapPin className="h-8 w-8 text-green-400" />
            </div>
          </div>
          
          <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">ETA Improvement</p>
                <p className="text-2xl font-bold text-white">2.5 hrs</p>
              </div>
              <Clock className="h-8 w-8 text-blue-400" />
            </div>
          </div>
          
          <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">Fuel Saved</p>
                <p className="text-2xl font-bold text-white">$284</p>
              </div>
              <DollarSign className="h-8 w-8 text-yellow-400" />
            </div>
          </div>
          
          <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">Orders Today</p>
                <p className="text-2xl font-bold text-white">24</p>
              </div>
              <Truck className="h-8 w-8 text-purple-400" />
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Upload Orders</h2>
            <p className="text-slate-400 mb-4">Upload CSV of orders to generate optimized routes</p>
            <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg">
              Upload CSV
            </button>
          </div>
          
          <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Route Preview</h2>
            <p className="text-slate-400 mb-4">View optimized routes and loading sequence</p>
            <div className="h-32 bg-slate-900 rounded border border-slate-600 flex items-center justify-center">
              <p className="text-slate-500">Map view placeholder</p>
            </div>
          </div>
        </div>
      </main>

      {/* Watermark */}
      <div className="fixed bottom-4 right-4 opacity-50">
        <div className="w-6 h-6 bg-blue-600 rounded flex items-center justify-center">
          <Truck className="h-4 w-4 text-white" />
        </div>
      </div>
    </div>
  )
}