import React, { useRef, useEffect, useState, useMemo } from 'react';
import './ScrollDatePicker.css';

const ScrollPicker = ({ options, value, onChange, placeholder }) => {
    const containerRef = useRef(null);
    const timeoutRef = useRef(null); // ✅ OPTIMIZATION: Track timeout for cleanup
    const [centerIndex, setCenterIndex] = useState(0);
    const [isExpanded, setIsExpanded] = useState(false);

    // Initialize center index based on value
    useEffect(() => {
        if (value) {
            const index = options.findIndex(opt => opt.value === value);
            if (index !== -1) {
                setCenterIndex(index);
            }
        }
    }, [value, options]);


    const handleScroll = (e) => {
        const container = e.target;
        const scrollTop = container.scrollTop;
        const itemHeight = 40;

        // Find which item center is closest to the highlight position (40px from top)
        // Item center = scrollTop + 40px (highlight position)
        const targetPosition = scrollTop + 40;
        const newCenterIndex = Math.floor(targetPosition / itemHeight);

        if (newCenterIndex !== centerIndex && newCenterIndex >= 0 && newCenterIndex < options.length) {
            setCenterIndex(newCenterIndex);
            onChange(options[newCenterIndex].value);
        }
    };

    const handleItemClick = (index) => {
        setCenterIndex(index);
        onChange(options[index].value);

        // Scroll to position item at 40px from top (center position)
        if (containerRef.current) {
            const itemHeight = 40;
            const scrollTo = (index * itemHeight) - itemHeight;
            containerRef.current.scrollTo({ top: scrollTo, behavior: 'smooth' });
        }

        // ✅ OPTIMIZATION: Clear existing timeout before setting new one
        if (timeoutRef.current) {
            clearTimeout(timeoutRef.current);
        }

        // Collapse picker after selection
        timeoutRef.current = setTimeout(() => {
            setIsExpanded(false);
        }, 300);
    };

    const handlePickerClick = () => {
        if (!isExpanded) {
            setIsExpanded(true);
            if (!value && options.length > 0) {
                // Mặc định chọn giá trị đầu tiên khi mở lần đầu
                const defaultIndex = 0;
                setCenterIndex(defaultIndex);
                onChange(options[defaultIndex].value);
            }
        }
    };

    // Auto-scroll to center the selected item when expanded
    useEffect(() => {
        if (containerRef.current && centerIndex >= 0 && isExpanded) {
            const itemHeight = 40;
            // Scroll so that centerIndex item appears at 40px from top (center position)
            const scrollTo = (centerIndex * itemHeight) - itemHeight;
            containerRef.current.scrollTo({ top: scrollTo, behavior: 'smooth' });
        }
    }, [centerIndex, isExpanded]);

    // ✅ OPTIMIZATION: Cleanup timeout on unmount
    useEffect(() => {
        return () => {
            if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
            }
        };
    }, []);


    return (
        <div
            className={`scroll-picker ${isExpanded ? 'expanded' : 'collapsed'}`}
            onClick={handlePickerClick}
        >
            {!isExpanded ? (
                <div className="scroll-picker-placeholder-collapsed">
                    {value ? (options.find(opt => opt.value === value)?.label || placeholder) : placeholder}
                </div>
            ) : (
                <div
                    className="scroll-picker-container"
                    ref={containerRef}
                    onScroll={handleScroll}
                    onClick={(e) => e.stopPropagation()}
                >
                    <div style={{ height: `${options.length * 40}px`, position: 'relative' }}>
                        {(() => {
                            // ✅ OPTIMIZATION: Calculate visible range ONCE instead of for every item
                            let visibleStart = centerIndex - 1;
                            let visibleEnd = centerIndex + 1;

                            // Adjust range if near the start
                            if (visibleStart < 0) {
                                visibleStart = 0;
                                visibleEnd = Math.min(2, options.length - 1);
                            }

                            // Adjust range if near the end
                            if (visibleEnd >= options.length) {
                                visibleEnd = options.length - 1;
                                visibleStart = Math.max(0, options.length - 3);
                            }

                            return options.map((option, index) => {
                                const isVisible = index >= visibleStart && index <= visibleEnd;

                                return (
                                    <div
                                        key={option.value}
                                        className={`scroll-picker-item ${index === centerIndex ? 'selected' : ''}`}
                                        style={{
                                            top: `${index * 40}px`,
                                            height: '40px',
                                            opacity: isVisible ? 1 : 0,
                                            pointerEvents: isVisible ? 'auto' : 'none'
                                        }}
                                        onClick={() => handleItemClick(index)}
                                    >
                                        {option.label}
                                    </div>
                                );
                            });
                        })()}
                    </div>
                </div>
            )}
        </div>
    );
};

// ✅ OPTIMIZATION: Static options - generated once, reused across all instances
const DAYS_OPTIONS = Array.from({ length: 31 }, (_, i) => ({
    value: i + 1,
    label: String(i + 1)
}));

const MONTHS_OPTIONS = [
    'Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6',
    'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12'
].map((month, index) => ({ value: index + 1, label: month }));

const ScrollDatePicker = ({ day, month, year, onDayChange, onMonthChange, onYearChange }) => {
    // ✅ OPTIMIZATION: Memoize years options (only when needed since it depends on current year)
    const years = useMemo(() => {
        const currentYear = new Date().getFullYear();
        return Array.from({ length: currentYear - 1940 }, (_, i) => ({
            value: currentYear - i,
            label: String(currentYear - i)
        }));
    }, []); // Empty deps - only calculate once

    return (
        <div className="scroll-date-picker">
            <ScrollPicker
                options={DAYS_OPTIONS}
                value={day}
                onChange={onDayChange}
                placeholder="Ngày"
            />
            <ScrollPicker
                options={MONTHS_OPTIONS}
                value={month}
                onChange={onMonthChange}
                placeholder="Tháng"
            />
            <ScrollPicker
                options={years}
                value={year}
                onChange={onYearChange}
                placeholder="Năm"
            />
        </div>
    );
};

export default ScrollDatePicker;
