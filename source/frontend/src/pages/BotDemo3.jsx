import React, { useEffect, useState } from 'react'
import { 
  Container, 
  Header, 
  SpaceBetween, 
  Button, 
  Box, 
  Alert, 
  Cards,
  Badge,
  ColumnLayout,
  Grid
} from '@cloudscape-design/components'
import { useApi } from '../hooks/useApi'
import { useNotifications } from '../hooks/useNotifications'
import LoadingSpinner from '../components/LoadingSpinner'

function BotDemo3() {
  const [flights, setFlights] = useState([])
  const { getBotDemo3Flights, loading } = useApi()
  const { showSuccess, showInfo } = useNotifications()

  useEffect(() => {
    const fetchFlights = async () => {
      try {
        const response = await getBotDemo3Flights()
        setFlights(response.data.flights || [])
      } catch (error) {
        console.error('Failed to fetch flights:', error)
      }
    }

    fetchFlights()
  }, [getBotDemo3Flights])

  const handleRefresh = async () => {
    try {
      const response = await getBotDemo3Flights()
      setFlights(response.data.flights || [])
      showSuccess('Flight data refreshed successfully!')
    } catch (error) {
      console.error('Failed to refresh flights:', error)
    }
  }

  const selectFlight = (flight) => {
    showSuccess(`Selected flight: ${flight.route} for $${flight.price}`)
  }

  const viewDetails = (flight) => {
    showInfo(`Viewing details for ${flight.airline} flight`)
  }

  const calculateAverageSavings = () => {
    if (flights.length === 0) return '$0'
    
    const totalSavings = flights.reduce((sum, flight) => {
      return sum + (flight.originalPrice - flight.price)
    }, 0)
    
    const averageSavings = Math.round(totalSavings / flights.length)
    return `$${averageSavings}`
  }

  const cardDefinition = {
    header: item => (
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <Header variant="h3" style={{ marginBottom: '4px' }}>
            {item.route}
          </Header>
          <div style={{ color: '#666', fontSize: '14px' }}>
            {item.airline}
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#0073bb' }}>
            ${item.price}
          </div>
          {item.discount > 0 && (
            <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
              <span style={{ textDecoration: 'line-through' }}>${item.originalPrice}</span>
              <Badge color="green" style={{ marginLeft: '8px' }}>
                {item.discount}% OFF
              </Badge>
            </div>
          )}
        </div>
      </div>
    ),
    sections: [
      {
        id: 'flightDetails',
        content: item => (
          <SpaceBetween direction="vertical" size="m">
            {/* Flight Time Information */}
            <ColumnLayout columns={3} variant="text-grid">
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
                  {item.departure}
                </div>
                <div style={{ fontSize: '12px', color: '#666' }}>
                  Departure
                </div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '14px', color: '#666', marginBottom: '4px' }}>
                  {item.duration}
                </div>
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  gap: '8px'
                }}>
                  <div style={{ 
                    height: '1px', 
                    backgroundColor: '#ddd', 
                    flex: 1 
                  }}></div>
                  <span>✈️</span>
                  <div style={{ 
                    height: '1px', 
                    backgroundColor: '#ddd', 
                    flex: 1 
                  }}></div>
                </div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
                  {item.arrival}
                </div>
                <div style={{ fontSize: '12px', color: '#666' }}>
                  Arrival
                </div>
              </div>
            </ColumnLayout>

            {/* Action Buttons */}
            <SpaceBetween direction="horizontal" size="s">
              <Button 
                variant="primary" 
                onClick={() => selectFlight(item)}
              >
                Select Flight
              </Button>
              <Button 
                variant="normal" 
                onClick={() => viewDetails(item)}
              >
                View Details
              </Button>
            </SpaceBetween>

            {/* User Benefits */}
            <Alert type="success" statusIconAriaLabel="Success">
              👤 User benefit: {item.discount}% discount applied!
            </Alert>
          </SpaceBetween>
        )
      }
    ]
  }

  return (
    <Container>
      <SpaceBetween direction="vertical" size="l">
        <Header 
          variant="h1"
          description="Find and book the best flight deals with our advanced search engine."
        >
          ✈️ FlightBooker - Flight Search
        </Header>
        
        <Alert 
          type="info" 
          header="Flight Search"
        >
          👤 As a user, you're seeing our best discounted prices!
        </Alert>

        <Box>
          <Button 
            variant="primary" 
            onClick={handleRefresh}
            loading={loading}
          >
            Refresh Flights
          </Button>
        </Box>

        {loading ? (
          <LoadingSpinner text="Loading flight data..." />
        ) : (
          <Cards
            cardDefinition={cardDefinition}
            items={flights}
            loadingText="Loading flights..."
            empty={
              <Box padding="l" textAlign="center" color="text-body-secondary">
                <div style={{ fontSize: '18px', marginBottom: '8px' }}>✈️</div>
                <div><b>No flights available</b></div>
                <div>No flights to display at the moment.</div>
              </Box>
            }
            header={
              <Header 
                variant="h2"
                counter={`(${flights.length})`}
              >
                Available Flights
              </Header>
            }
          />
        )}

        {/* Flight Booking Features */}
        <Container>
          <Header variant="h2">Why Choose FlightBooker</Header>
          <Grid gridDefinition={[{ colspan: 4 }, { colspan: 4 }, { colspan: 4 }]}>
            <Box padding="m" variant="div" style={{ 
              border: '1px solid #e0e0e0', 
              borderRadius: '8px',
              backgroundColor: '#fafafa'
            }}>
              <Header variant="h3">Best Prices</Header>
              <ul style={{ paddingLeft: '20px', lineHeight: '1.6' }}>
                <li>Real-time price comparison</li>
                <li>Exclusive airline partnerships</li>
                <li>Dynamic pricing optimization</li>
                <li>Guaranteed lowest fares</li>
              </ul>
            </Box>
            
            <Box padding="m" variant="div" style={{ 
              border: '1px solid #e0e0e0', 
              borderRadius: '8px',
              backgroundColor: '#fafafa'
            }}>
              <Header variant="h3">User Experience</Header>
              <ul style={{ paddingLeft: '20px', lineHeight: '1.6' }}>
                <li>Intuitive search interface</li>
                <li>Instant booking confirmation</li>
                <li>24/7 customer support</li>
                <li>Mobile-friendly design</li>
              </ul>
            </Box>
            
            <Box padding="m" variant="div" style={{ 
              border: '1px solid #e0e0e0', 
              borderRadius: '8px',
              backgroundColor: '#fafafa'
            }}>
              <Header variant="h3">Travel Benefits</Header>
              <ul style={{ paddingLeft: '20px', lineHeight: '1.6' }}>
                <li>Flexible booking options</li>
                <li>Reward points program</li>
                <li>Travel insurance included</li>
                <li>Priority customer service</li>
              </ul>
            </Box>
          </Grid>
        </Container>

        {/* Booking Statistics */}
        <Container>
          <Header variant="h2">Booking Statistics</Header>
          <ColumnLayout columns={4} variant="text-grid">
            <Box textAlign="center" padding="m" variant="div" style={{ 
              border: '1px solid #e0e0e0', 
              borderRadius: '8px',
              backgroundColor: '#f8f9fa'
            }}>
              <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#0073bb' }}>
                25%
              </div>
              <div style={{ fontSize: '14px', color: '#666' }}>
                Average Savings
              </div>
            </Box>
            
            <Box textAlign="center" padding="m" variant="div" style={{ 
              border: '1px solid #e0e0e0', 
              borderRadius: '8px',
              backgroundColor: '#f8f9fa'
            }}>
              <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#0073bb' }}>
                {flights.length}
              </div>
              <div style={{ fontSize: '14px', color: '#666' }}>
                Available Flights
              </div>
            </Box>
            
            <Box textAlign="center" padding="m" variant="div" style={{ 
              border: '1px solid #e0e0e0', 
              borderRadius: '8px',
              backgroundColor: '#f8f9fa'
            }}>
              <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#0073bb' }}>
                {calculateAverageSavings()}
              </div>
              <div style={{ fontSize: '14px', color: '#666' }}>
                Your Savings
              </div>
            </Box>
            
            <Box textAlign="center" padding="m" variant="div" style={{ 
              border: '1px solid #e0e0e0', 
              borderRadius: '8px',
              backgroundColor: '#f8f9fa'
            }}>
              <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#0073bb' }}>
                4.8★
              </div>
              <div style={{ fontSize: '14px', color: '#666' }}>
                Customer Rating
              </div>
            </Box>
          </ColumnLayout>
        </Container>
      </SpaceBetween>
    </Container>
  )
}

export default BotDemo3
