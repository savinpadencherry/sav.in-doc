import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Upload, FileText, MapPin, Clock, Package } from "lucide-react"

export default function OrdersPage() {
  const sampleOrders = [
    {
      id: "ORD-001",
      customer: "ACME Corp",
      address: "123 Main St, Boston, MA",
      weight: "150.5 kg",
      priority: "High",
      timeWindow: "08:00 - 17:00",
      status: "Pending"
    },
    {
      id: "ORD-002", 
      customer: "TechFlow Inc",
      address: "456 Tech Ave, Cambridge, MA",
      weight: "89.2 kg",
      priority: "Medium",
      timeWindow: "09:00 - 16:00",
      status: "Scheduled"
    },
    {
      id: "ORD-003",
      customer: "Global Supplies", 
      address: "789 Industrial Rd, Worcester, MA",
      weight: "234.7 kg",
      priority: "High",
      timeWindow: "07:30 - 15:30",
      status: "In Transit"
    }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700 bg-slate-900/50 backdrop-blur">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <Package className="h-5 w-5 text-white" />
            </div>
            <h1 className="text-xl font-bold text-white">ChainSync - Orders</h1>
          </div>
          <nav className="hidden md:flex space-x-6">
            <a href="/" className="text-slate-300 hover:text-white">Dashboard</a>
            <a href="/orders" className="text-blue-400 hover:text-blue-300">Orders</a>
            <a href="/planner" className="text-slate-300 hover:text-white">Planner</a>
            <a href="/routes" className="text-slate-300 hover:text-white">Routes</a>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Upload Section */}
        <Card className="mb-8 bg-slate-800/50 backdrop-blur border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Upload className="h-5 w-5" />
              Upload Orders
            </CardTitle>
            <CardDescription>
              Import orders from CSV file to start route optimization
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="border-2 border-dashed border-slate-600 rounded-lg p-8 text-center">
              <FileText className="h-12 w-12 text-slate-400 mx-auto mb-4" />
              <p className="text-slate-300 mb-4">Drag and drop your CSV file here, or click to browse</p>
              <Button className="bg-blue-600 hover:bg-blue-700">
                Choose File
              </Button>
              <p className="text-sm text-slate-500 mt-2">
                Supported format: CSV with columns: customer, address, lat, lng, weight, volume, priority
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Orders Table */}
        <Card className="bg-slate-800/50 backdrop-blur border-slate-700">
          <CardHeader>
            <CardTitle className="text-white">Current Orders</CardTitle>
            <CardDescription>
              {sampleOrders.length} orders ready for optimization
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-600">
                    <th className="text-left py-3 px-4 text-slate-300 font-medium">Order ID</th>
                    <th className="text-left py-3 px-4 text-slate-300 font-medium">Customer</th>
                    <th className="text-left py-3 px-4 text-slate-300 font-medium">Address</th>
                    <th className="text-left py-3 px-4 text-slate-300 font-medium">Weight</th>
                    <th className="text-left py-3 px-4 text-slate-300 font-medium">Priority</th>
                    <th className="text-left py-3 px-4 text-slate-300 font-medium">Time Window</th>
                    <th className="text-left py-3 px-4 text-slate-300 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {sampleOrders.map((order) => (
                    <tr key={order.id} className="border-b border-slate-700 hover:bg-slate-700/30">
                      <td className="py-3 px-4 text-blue-400 font-mono">{order.id}</td>
                      <td className="py-3 px-4 text-white">{order.customer}</td>
                      <td className="py-3 px-4 text-slate-300 flex items-center gap-1">
                        <MapPin className="h-4 w-4 text-slate-500" />
                        {order.address}
                      </td>
                      <td className="py-3 px-4 text-slate-300">{order.weight}</td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          order.priority === 'High' 
                            ? 'bg-red-900/50 text-red-300' 
                            : order.priority === 'Medium'
                            ? 'bg-yellow-900/50 text-yellow-300'
                            : 'bg-green-900/50 text-green-300'
                        }`}>
                          {order.priority}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-300 flex items-center gap-1">
                        <Clock className="h-4 w-4 text-slate-500" />
                        {order.timeWindow}
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          order.status === 'Pending'
                            ? 'bg-slate-700 text-slate-300'
                            : order.status === 'Scheduled'
                            ? 'bg-blue-900/50 text-blue-300'
                            : 'bg-green-900/50 text-green-300'
                        }`}>
                          {order.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            <div className="flex justify-between items-center mt-6">
              <p className="text-slate-400 text-sm">
                Showing {sampleOrders.length} of {sampleOrders.length} orders
              </p>
              <Button className="bg-blue-600 hover:bg-blue-700">
                Optimize Routes
              </Button>
            </div>
          </CardContent>
        </Card>
      </main>

      {/* Watermark */}
      <div className="fixed bottom-4 right-4 opacity-50">
        <div className="w-6 h-6 bg-blue-600 rounded flex items-center justify-center">
          <Package className="h-4 w-4 text-white" />
        </div>
      </div>
    </div>
  )
}