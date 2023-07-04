package main

import "time"

type Cache struct {
	Store map[string]CacheValue
}

type CacheValue struct {
	Value      string
	ExpireTime time.Time
}

func (c Cache) ClearExpired() {
	for key, value := range c.Store {
		if value.ExpireTime.Before(time.Now()) {
			delete(c.Store, key)
		}
	}
}

func (c Cache) Get(key string) *CacheValue {
	if val, ok := c.Store[key]; ok {
		return &val
	}

	return nil
}

func (c Cache) Set(key string, value string, expireTime time.Duration) {
	c.Store[key] = CacheValue{
		Value:      value,
		ExpireTime: time.Now().Add(expireTime),
	}
}
