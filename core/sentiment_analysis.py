import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import numpy as np
from typing import Dict, Tuple
from datetime import datetime, timedelta
from django.db.models import QuerySet
from .models import IssuerNews

class NewsSentimentAnalyzer:
    def __init__(self):
        try:
            nltk.data.find('sentiment/vader_lexicon.zip')
        except LookupError:
            nltk.download('vader_lexicon')
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
    
    def analyze_text(self, text: str) -> Dict[str, float]:
        """Analyze sentiment of a single text."""
        scores = self.sentiment_analyzer.polarity_scores(text)
        
        # Convert compound score (-1 to 1) to a sentiment label
        compound = scores['compound']
        if compound >= 0.05:
            sentiment = 'positive'
        elif compound <= -0.05:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
            
        # Convert compound score to confidence percentage
        confidence = abs(compound) * 100
        
        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'score': compound
        }
    
    def analyze_news(self, news_items: QuerySet) -> Dict[str, any]:
        """Analyze sentiment for a collection of news items."""
        if not news_items:
            return {
                'overall_sentiment': 'neutral',
                'confidence': 0,
                'sentiment_distribution': {'positive': 0, 'neutral': 0, 'negative': 0},
                'trading_signal': 'HOLD'
            }
        
        sentiments = []
        for news in news_items:
            # Analyze both title and content
            title_sentiment = self.analyze_text(news.title)
            content_sentiment = self.analyze_text(news.content)
            
            # Weighted average (title has more weight as it's more concise)
            combined_score = (title_sentiment['score'] * 0.4 + content_sentiment['score'] * 0.6)
            sentiments.append({
                'score': combined_score,
                'date': news.published_date,
                'sentiment': 'positive' if combined_score > 0.05 else 'negative' if combined_score < -0.05 else 'neutral'
            })
        
        # Calculate time-weighted scores (more recent news has more impact)
        now = datetime.now()
        max_days = 30  # Consider news up to 30 days old
        weighted_scores = []
        
        for s in sentiments:
            days_old = (now - s['date'].replace(tzinfo=None)).days
            if days_old <= max_days:
                time_weight = 1 - (days_old / max_days)
                weighted_scores.append(s['score'] * time_weight)
        
        if not weighted_scores:
            return {
                'overall_sentiment': 'neutral',
                'confidence': 0,
                'sentiment_distribution': {'positive': 0, 'neutral': 0, 'negative': 0},
                'trading_signal': 'HOLD'
            }
        
        # Calculate overall sentiment
        avg_score = np.mean(weighted_scores)
        sentiment_strength = abs(avg_score)
        overall_sentiment = 'positive' if avg_score > 0.05 else 'negative' if avg_score < -0.05 else 'neutral'
        
        # Calculate sentiment distribution
        sentiment_counts = {'positive': 0, 'neutral': 0, 'negative': 0}
        for s in sentiments:
            sentiment_counts[s['sentiment']] += 1
        total = len(sentiments)
        sentiment_distribution = {k: (v/total)*100 for k, v in sentiment_counts.items()}
        
        # Calculate confidence based on sentiment strength and consistency
        sentiment_confidence = sentiment_strength * 100  # Convert to percentage
        
        # Determine trading signal
        if overall_sentiment == 'positive' and sentiment_confidence > 60:
            trading_signal = 'BUY'
        elif overall_sentiment == 'negative' and sentiment_confidence > 60:
            trading_signal = 'SELL'
        else:
            trading_signal = 'HOLD'
        
        return {
            'overall_sentiment': overall_sentiment,
            'confidence': sentiment_confidence,
            'sentiment_distribution': sentiment_distribution,
            'trading_signal': trading_signal
        }

def get_news_sentiment_signal(issuer_code: str) -> Tuple[str, float]:
    """Get trading signal based on news sentiment for a given issuer."""
    analyzer = NewsSentimentAnalyzer()
    
    # Get recent news (last 30 days)
    recent_news = IssuerNews.objects.filter(
        issuer__code=issuer_code,
        published_date__gte=datetime.now() - timedelta(days=30)
    ).order_by('-published_date')
    
    analysis = analyzer.analyze_news(recent_news)
    return analysis['trading_signal'], analysis['confidence'] 