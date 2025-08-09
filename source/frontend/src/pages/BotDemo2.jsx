import React, { useEffect, useState } from 'react'
import { Container, Header, SpaceBetween, Button, Box, Alert, FormField, Input, Textarea, ColumnLayout } from '@cloudscape-design/components'
import { useApi } from '../hooks/useApi'
import { useNotifications } from '../hooks/useNotifications'
import LoadingSpinner from '../components/LoadingSpinner'

function BotDemo2() {
  const [reviews, setReviews] = useState([])
  const [newReview, setNewReview] = useState({ name: '', rating: 5, comment: '' })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { getBotDemo2Comments, postBotDemo2Comment, loading } = useApi()
  const { showSuccess, showError } = useNotifications()

  // Mock hotel data with real image
  const hotelData = {
    name: "Grand Azure Resort & Spa",
    location: "Santorini, Greece",
    rating: 4.2,
    totalReviews: 1247,
    pricePerNight: 285,
    imageUrl: "https://cache.marriott.com/is/image/marriotts7prod/lc-jtrml-mystique-overview-39985:Wide-Hor?wid=750&fit=constrain",
    facilities: [
      "Infinity Pool",
      "Fine Dining",
      "Full-Service Spa", 
      "Fitness Center",
      "Free Parking",
      "Free WiFi",
      "Private Beach",
      "Airport Shuttle"
    ]
  }

  useEffect(() => {
    const fetchReviews = async () => {
      try {
        const response = await getBotDemo2Comments()
        setReviews(response.data.comments || [])
      } catch (error) {
        console.error('Failed to fetch reviews:', error)
      }
    }

    fetchReviews()
  }, [getBotDemo2Comments])

  const handleSubmitReview = async (e) => {
    e.preventDefault()
    if (!newReview.name || !newReview.comment) return

    try {
      setIsSubmitting(true)
      await postBotDemo2Comment({
        name: newReview.name,
        comment: newReview.comment,
        rating: newReview.rating
      })
      showSuccess('Review submitted successfully!')
      setNewReview({ name: '', rating: 5, comment: '' })
      
      // Refresh reviews
      const response = await getBotDemo2Comments()
      setReviews(response.data.comments || [])
    } catch (error) {
      showError('Failed to submit review')
    } finally {
      setIsSubmitting(false)
    }
  }

  const renderStars = (rating) => {
    return Array.from({ length: 5 }, (_, i) => (
      <span key={i} style={{ color: i < rating ? '#FF9500' : '#E0E0E0', fontSize: '18px' }}>
        ★
      </span>
    ))
  }

  const renderRatingSelector = () => {
    return (
      <div style={{ display: 'flex', gap: '5px', alignItems: 'center' }}>
        {Array.from({ length: 5 }, (_, i) => (
          <button
            key={i}
            type="button"
            onClick={() => setNewReview(prev => ({ ...prev, rating: i + 1 }))}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              fontSize: '24px',
              color: i < newReview.rating ? '#FF9500' : '#E0E0E0',
              padding: '2px'
            }}
          >
            ★
          </button>
        ))}
        <span style={{ marginLeft: '10px', fontSize: '14px', color: '#666' }}>
          ({newReview.rating} star{newReview.rating !== 1 ? 's' : ''})
        </span>
      </div>
    )
  }

  return (
    <Container>
      <SpaceBetween direction="vertical" size="l">
        <Header variant="h1">🏨 TravelBooker - Hotel Reviews</Header>
        
        <Alert type="info" header="Bot Detection Demo">
          This simulates a hotel booking platform where bot reviews are silently discarded while appearing successful to the bot.
        </Alert>

        {/* Hotel Information Card */}
        <Container>
          <ColumnLayout columns={2}>
            <div>
              <img 
                src={hotelData.imageUrl} 
                alt={hotelData.name}
                style={{ 
                  width: '100%', 
                  height: '200px', 
                  objectFit: 'cover', 
                  borderRadius: '8px',
                  border: '1px solid #e0e0e0'
                }}
              />
            </div>
            <SpaceBetween direction="vertical" size="s">
              <Header variant="h2">{hotelData.name}</Header>
              <Box>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                  {renderStars(Math.floor(hotelData.rating))}
                  <span style={{ fontWeight: 'bold', fontSize: '16px' }}>{hotelData.rating}</span>
                  <span style={{ color: '#666', fontSize: '14px' }}>({hotelData.totalReviews} reviews)</span>
                </div>
                <div style={{ color: '#666', marginBottom: '12px' }}>📍 {hotelData.location}</div>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#0073bb' }}>
                  ${hotelData.pricePerNight} <span style={{ fontSize: '14px', fontWeight: 'normal' }}>per night</span>
                </div>
              </Box>
            </SpaceBetween>
          </ColumnLayout>
        </Container>

        {/* Hotel Facilities */}
        <Container>
          <Header variant="h3">Hotel Facilities</Header>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {hotelData.facilities.map((facility, index) => (
              <span
                key={index}
                style={{
                  display: 'inline-block',
                  padding: '6px 12px',
                  backgroundColor: '#f0f8ff',
                  color: '#0073bb',
                  borderRadius: '16px',
                  fontSize: '14px',
                  fontWeight: '500',
                  border: '1px solid #d6ebff'
                }}
              >
                {facility}
              </span>
            ))}
          </div>
        </Container>

        {/* Review Form */}
        <Container>
          <Header variant="h3">Share Your Experience</Header>
          <form onSubmit={handleSubmitReview}>
            <SpaceBetween direction="vertical" size="m">
              <FormField label="Your Name">
                <Input
                  value={newReview.name}
                  onChange={({ detail }) => setNewReview(prev => ({ ...prev, name: detail.value }))}
                  placeholder="Enter your name"
                />
              </FormField>
              
              <FormField label="Rating">
                {renderRatingSelector()}
              </FormField>
              
              <FormField label="Review">
                <Textarea
                  value={newReview.comment}
                  onChange={({ detail }) => setNewReview(prev => ({ ...prev, comment: detail.value }))}
                  placeholder="Tell us about your stay at Grand Azure Resort & Spa..."
                  rows={4}
                />
              </FormField>
              
              <Button 
                variant="primary" 
                type="submit"
                loading={isSubmitting}
                disabled={!newReview.name || !newReview.comment}
              >
                Submit Review
              </Button>
            </SpaceBetween>
          </form>
        </Container>

        {/* Reviews Display */}
        <Container>
          <Header variant="h3">Guest Reviews ({reviews.length})</Header>
          {loading ? (
            <LoadingSpinner text="Loading reviews..." />
          ) : (
            <SpaceBetween direction="vertical" size="m">
              {reviews.map((review, index) => (
                <Box key={index} padding="m" variant="div" style={{ 
                  border: '1px solid #e0e0e0', 
                  borderRadius: '8px',
                  backgroundColor: '#fafafa'
                }}>
                  <SpaceBetween direction="vertical" size="xs">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <strong style={{ fontSize: '16px' }}>{review.name}</strong>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                        {renderStars(review.rating || 5)}
                        <span style={{ fontSize: '14px', color: '#666' }}>
                          {review.rating || 5}/5
                        </span>
                      </div>
                    </div>
                    <div style={{ color: '#333', lineHeight: '1.5' }}>{review.comment}</div>
                    <div style={{ color: '#999', fontSize: '12px' }}>
                      Verified Guest • {new Date().toLocaleDateString()}
                    </div>
                  </SpaceBetween>
                </Box>
              ))}
              {reviews.length === 0 && (
                <Box padding="l" textAlign="center" color="text-body-secondary">
                  <div style={{ fontSize: '18px', marginBottom: '8px' }}>✍️</div>
                  <div>No reviews yet. Be the first to share your experience!</div>
                </Box>
              )}
            </SpaceBetween>
          )}
        </Container>
      </SpaceBetween>
    </Container>
  )
}

export default BotDemo2
