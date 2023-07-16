package main

import "time"

type Cache struct {
	Store map[string]CacheValue
}

type CacheValue struct {
	Value       string
	ExpireTime  int64
	IsBlockOnly bool
}

// This should run in a go routine following the latest block.
func (c Cache) ClearExpired(isNewBlock bool) int {
	delKeys := 0
	now := time.Now().Unix()

	for key, value := range c.Store {
		if value.IsBlockOnly && isNewBlock {
			delKeys++
			delete(c.Store, key)
			continue
		}

		if value.ExpireTime < now {
			delKeys++
			delete(c.Store, key)
		}
	}

	return delKeys
}

func (c Cache) Keys() []string {
	keys := make([]string, 0, len(c.Store))
	for k := range c.Store {
		keys = append(keys, k)
	}

	return keys
}

func (c Cache) Get(key string) *CacheValue {
	if val, ok := c.Store[key]; ok {
		now := time.Now()
		if val.ExpireTime < now.Unix() {
			delete(c.Store, key)
			return nil
		}

		return &val
	}

	return nil
}

func (c Cache) Set(key string, value string, expireSeconds int) {
	if expireSeconds == 0 {
		return
	}

	isBlockOnly := false
	if expireSeconds == -2 {
		isBlockOnly = true
		expireSeconds = DefaultCacheTimeSeconds
	}

	now := time.Now()
	expireTime := now.Add(time.Duration(expireSeconds) * time.Second).Unix()

	c.Store[key] = CacheValue{
		Value:       value,
		ExpireTime:  expireTime,
		IsBlockOnly: isBlockOnly,
	}
}
