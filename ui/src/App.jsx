import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './App.css'
import Dashboard from './Components/Dashboard'
import Overview from './Components/Overview'
import Transactions from './components/Transactions'
import Budgeting from './Components/Budgeting'
import ChatComponent from './Components/ChatComponent'


function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />}>
          <Route index element={<Overview />} />
          <Route path="transactions" element={<Transactions />} />
          <Route path="budgeting" element={<Budgeting />} />
          <Route path="chat" element={<ChatComponent />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
