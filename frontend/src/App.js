import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from "./components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./components/ui/table"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select"
import { Button } from "./components/ui/button"
import { Calendar } from "./components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "./components/ui/popover"
import { Switch } from "./components/ui/switch"
import { format } from "date-fns"
import { CheckCircle, XCircle, AlertTriangle, AlertCircle, Loader2 } from 'lucide-react';

axios.defaults.baseURL = 'http://localhost:5000';

function App() {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedTenant, setSelectedTenant] = useState('');
  const [tenants, setTenants] = useState([]);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [statusFilter, setStatusFilter] = useState('all');
  const [showActiveOnly, setShowActiveOnly] = useState(false);
  const [updatingDevices, setUpdatingDevices] = useState(new Set());

  const fetchTenants = useCallback(async () => {
    try {
      const response = await axios.get('/api/tenants');
      // Filter out any empty tenant names and ensure unique values
      const filteredTenants = [...new Set(response.data.filter(tenant => tenant && tenant.trim() !== ''))];
      setTenants(filteredTenants);
    } catch (err) {
      console.error('Error fetching tenants:', err);
      setError('Error fetching tenants. Please try again later.');
    }
  }, []);

  const fetchDevices = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get('/api/devices', {
        params: {
          tenant: selectedTenant,
          date: format(selectedDate, 'yyyy-MM-dd'),
        }
      });
      setDevices(response.data);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching devices:', err);
      setError('Error fetching devices. Please try again later.');
      setLoading(false);
    }
  }, [selectedTenant, selectedDate]);

  useEffect(() => {
    fetchTenants();
  }, [fetchTenants]);

  useEffect(() => {
    fetchDevices();
  }, [fetchDevices]);

  const filteredDevices = devices.filter(device => 
    (statusFilter === 'all' || device.status === statusFilter) &&
    (!showActiveOnly || device.active)
  );

  const getChartData = () => {
    const statusCounts = filteredDevices.reduce((acc, device) => {
      acc[device.status] = (acc[device.status] || 0) + 1;
      return acc;
    }, {});

    return Object.keys(statusCounts).map(status => ({
      name: status,
      count: statusCounts[status]
    }));
  };

  const getTotalDevices = () => filteredDevices.length;
  const getDevicesByStatus = (status) => filteredDevices.filter(device => device.status === status).length;

  const statusFilters = [
    { key: 'all', label: 'All' },
    { key: 'OK', label: 'OK' },
    { key: 'Warning', label: 'Warnings' },
    { key: 'Error', label: 'Errors' },
  ];

  const getStatusIcon = (status) => {
    switch (status) {
      case 'OK': return <CheckCircle className="text-green-500" />;
      case 'Warning': return <AlertTriangle className="text-yellow-500" />;
      case 'Error': return <XCircle className="text-red-500" />;
      default: return <AlertCircle className="text-blue-500" />;
    }
  };

  const formatDate = (dateString) => {
    if (dateString === 'Never') return 'Never';
    const date = new Date(dateString);
    return isNaN(date.getTime()) ? 'Invalid Date' : format(date, 'yyyy-MM-dd HH:mm');
  };

  const toggleDeviceActive = useCallback(async (deviceName) => {
    setUpdatingDevices(prev => new Set(prev).add(deviceName));
    try {
      const device = devices.find(d => d.name === deviceName);
      const newActiveState = !device.active;
      
      // Make API call to update device status
      await axios.post('/api/devices/update_status', { 
        name: deviceName, 
        active: newActiveState 
      });

      // Update local state
      setDevices(prevDevices => 
        prevDevices.map(d => 
          d.name === deviceName 
            ? { ...d, active: newActiveState } 
            : d
        )
      );
    } catch (err) {
      console.error('Error updating device status:', err);
      setError('Error updating device status. Please try again later.');
    } finally {
      setUpdatingDevices(prev => {
        const newSet = new Set(prev);
        newSet.delete(deviceName);
        return newSet;
      });
    }
  }, [devices]);

  if (loading) return <div className="flex items-center justify-center h-screen">Loading...</div>;
  if (error) return <div className="flex items-center justify-center h-screen text-red-500">{error}</div>;

  return (
    <div className="container mx-auto p-6 space-y-8 bg-gray-50 min-h-screen">
      <h1 className="text-4xl font-bold mb-8 text-center text-gray-800">Acronis Backup Dashboard</h1>
      
      <div className="flex justify-between items-center mb-6">
        <Select onValueChange={setSelectedTenant} value={selectedTenant}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Select tenant" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Tenants</SelectItem>
            {tenants.map(tenant => (
              tenant && tenant.trim() !== '' && <SelectItem key={tenant} value={tenant}>{tenant}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Popover>
          <PopoverTrigger asChild>
            <Button variant="outline">{format(selectedDate, 'PP')}</Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0">
            <Calendar
              mode="single"
              selected={selectedDate}
              onSelect={setSelectedDate}
              initialFocus
            />
          </PopoverContent>
        </Popover>

        <div className="flex items-center space-x-2">
          <span>Show Active Only</span>
          <Switch
            checked={showActiveOnly}
            onCheckedChange={setShowActiveOnly}
          />
        </div>
      </div>

      <div className="flex space-x-2 mb-6">
        {statusFilters.map(filter => (
          <Button 
            key={filter.key}
            variant={statusFilter === filter.key ? 'default' : 'outline'}
            onClick={() => setStatusFilter(filter.key)}
          >
            {filter.label}
          </Button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {[
          { title: "Total Devices", value: getTotalDevices(), color: "blue" },
          { title: "OK", value: getDevicesByStatus('OK'), color: "green" },
          { title: "Warnings", value: getDevicesByStatus('Warning'), color: "yellow" },
          { title: "Errors", value: getDevicesByStatus('Error'), color: "red" },
        ].map((item) => (
          <Card key={item.title}>
            <CardHeader>
              <CardTitle>{item.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className={`text-4xl font-bold text-${item.color}-600`}>{item.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Device Status Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={getChartData()} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Device List</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Device Name</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Last Backup</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredDevices.map((device) => (
                <TableRow key={device.name}>
                  <TableCell>{device.name}</TableCell>
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(device.status)}
                      <span>{device.status}</span>
                    </div>
                  </TableCell>
                  <TableCell>{formatDate(device.lastBackup)}</TableCell>
                  <TableCell>{device.type}</TableCell>
                  <TableCell>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => toggleDeviceActive(device.name)}
                      disabled={updatingDevices.has(device.name)}
                    >
                      {updatingDevices.has(device.name) ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : null}
                      {device.active ? 'Active' : 'Inactive'}
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

export default App;
