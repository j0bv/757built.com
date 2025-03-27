"use client"

import { useState, useRef, useEffect } from "react"
import { ChevronDown } from "lucide-react"
import { cn } from "@/lib/utils"

import { Button } from "@/components/ui/button"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { YearSelector } from "./year-selector"

// Sample data - in a real app, this would come from an API
const sampleData = {
  2023: {
    total: 12,
    contributions: [
      { date: "2023-01-05", count: 1 },
      { date: "2023-02-15", count: 2 },
      { date: "2023-04-10", count: 3 },
      { date: "2023-06-22", count: 1 },
      { date: "2023-08-30", count: 2 },
      { date: "2023-09-15", count: 1 },
      { date: "2023-10-12", count: 3 },
      { date: "2023-11-12", count: 3 },
    ],
  },
  2024: {
    total: 8,
    contributions: [
      { date: "2024-01-20", count: 2 },
      { date: "2024-03-15", count: 1 },
      { date: "2024-05-10", count: 3 },
      { date: "2024-07-05", count: 2 },
      { date: "2024-08-12", count: 1 },
      { date: "2024-10-25", count: 2 },
      { date: "2024-12-01", count: 3 },
    ],
  },
  2025: {
    total: 10,
    contributions: [
      { date: "2025-01-15", count: 1 },
      { date: "2025-03-10", count: 1 },
      { date: "2025-03-27", count: 3 },
      { date: "2025-05-05", count: 1 },
      { date: "2025-07-20", count: 2 },
      { date: "2025-08-15", count: 1 },
      { date: "2025-10-10", count: 3 },
      { date: "2025-11-25", count: 2 },
      { date: "2025-12-24", count: 1 },
    ],
  },
  2030: {
    total: 5,
    contributions: [
      { date: "2030-01-10", count: 1 },
      { date: "2030-02-20", count: 2 },
      { date: "2030-03-15", count: 1 },
      { date: "2030-04-05", count: 3 },
      { date: "2030-05-12", count: 2 },
    ],
  },
}

export function StretchCalendarHeatmap() {
  const [currentYear, setCurrentYear] = useState(2030)
  const [tooltipContent, setTooltipContent] = useState(null)
  const [activeCell, setActiveCell] = useState(null)
  const [scrollPosition, setScrollPosition] = useState(0) // 0 = Jan-Jun, 1 = Jul-Dec
  const [containerWidth, setContainerWidth] = useState(0)
  const scrollTrackRef = useRef(null)
  const scrollThumbRef = useRef(null)
  const containerRef = useRef(null)
  const isDraggingRef = useRef(false)
  const startXRef = useRef(0)
  const startLeftRef = useRef(0)

  // Get months and weekdays
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
  const weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
  const visibleWeekdays = ["Mon", "Wed", "Fri"] // Only show these weekdays to match the example

  // Get visible months based on scroll position
  const visibleMonths = scrollPosition === 0 ? months.slice(0, 6) : months.slice(6, 12)

  // Get contribution level (0-4) based on count
  const getContributionLevel = (count) => {
    if (count === 0) return 0
    if (count === 1) return 1
    if (count === 2) return 2
    if (count <= 4) return 3
    return 4
  }

  // Get color class based on contribution level
  const getColorClass = (level) => {
    switch (level) {
      case 0:
        return "bg-gray-800"
      case 1:
        return "bg-green-900"
      case 2:
        return "bg-green-700"
      case 3:
        return "bg-green-500"
      case 4:
        return "bg-green-300"
      default:
        return "bg-gray-800"
    }
  }

  // Generate calendar data
  const generateCalendarData = () => {
    const yearData = sampleData[currentYear] || { total: 0, contributions: [] }
    const contributionMap = {}

    // Create a map of contributions by date
    yearData.contributions.forEach((item) => {
      contributionMap[item.date] = item.count
    })

    return {
      total: yearData.total,
      contributionMap,
    }
  }

  const { total, contributionMap } = generateCalendarData()

  // Format date string
  const formatDateString = (year, month, day) => {
    return `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`
  }

  // Handle mouse enter on contribution cell
  const handleCellMouseEnter = (year, month, day, count) => {
    if (count > 0) {
      const date = new Date(year, month, day)
      const formattedDate = date.toLocaleDateString("en-US", { month: "long", day: "numeric" })
      setTooltipContent(
        `${count} contribution${count !== 1 ? "s" : ""} on ${formattedDate} ${day}${getDaySuffix(day)}.`,
      )
      setActiveCell(`${year}-${month}-${day}`)
    }
  }

  // Get day suffix (st, nd, rd, th)
  const getDaySuffix = (day) => {
    if (day > 3 && day < 21) return "th"
    switch (day % 10) {
      case 1:
        return "st"
      case 2:
        return "nd"
      case 3:
        return "rd"
      default:
        return "th"
    }
  }

  // Navigate to previous year
  const goToPreviousYear = () => {
    setCurrentYear((prev) => prev - 1)
  }

  // Navigate to next year
  const goToNextYear = () => {
    setCurrentYear((prev) => prev + 1)
  }

  // Handle scroll thumb drag
  const handleMouseDown = (e) => {
    isDraggingRef.current = true
    startXRef.current = e.clientX
    startLeftRef.current = scrollThumbRef.current.offsetLeft
    document.addEventListener("mousemove", handleMouseMove)
    document.addEventListener("mouseup", handleMouseUp)
  }

  const handleMouseMove = (e) => {
    if (!isDraggingRef.current) return

    const trackRect = scrollTrackRef.current.getBoundingClientRect()
    const thumbRect = scrollThumbRef.current.getBoundingClientRect()
    const trackWidth = trackRect.width
    const thumbWidth = thumbRect.width
    const maxLeft = trackWidth - thumbWidth

    let newLeft = startLeftRef.current + (e.clientX - startXRef.current)
    newLeft = Math.max(0, Math.min(newLeft, maxLeft))

    scrollThumbRef.current.style.left = `${newLeft}px`

    // Update scroll position based on thumb position
    if (newLeft > maxLeft / 2) {
      setScrollPosition(1) // Jul-Dec
    } else {
      setScrollPosition(0) // Jan-Jun
    }
  }

  const handleMouseUp = () => {
    isDraggingRef.current = false
    document.removeEventListener("mousemove", handleMouseMove)
    document.removeEventListener("mouseup", handleMouseUp)

    // Snap to position
    const trackRect = scrollTrackRef.current.getBoundingClientRect()
    const thumbRect = scrollThumbRef.current.getBoundingClientRect()
    const trackWidth = trackRect.width
    const thumbWidth = thumbRect.width
    const maxLeft = trackWidth - thumbWidth

    if (scrollPosition === 1) {
      scrollThumbRef.current.style.left = `${maxLeft}px`
    } else {
      scrollThumbRef.current.style.left = "0px"
    }
  }

  // Handle click on track
  const handleTrackClick = (e) => {
    const trackRect = scrollTrackRef.current.getBoundingClientRect()
    const thumbRect = scrollThumbRef.current.getBoundingClientRect()
    const trackWidth = trackRect.width
    const thumbWidth = thumbRect.width
    const maxLeft = trackWidth - thumbWidth
    const clickX = e.clientX - trackRect.left

    if (clickX > trackWidth / 2) {
      setScrollPosition(1) // Jul-Dec
      scrollThumbRef.current.style.left = `${maxLeft}px`
    } else {
      setScrollPosition(0) // Jan-Jun
      scrollThumbRef.current.style.left = "0px"
    }
  }

  // Update container width on resize
  useEffect(() => {
    const updateWidth = () => {
      if (containerRef.current) {
        const width = containerRef.current.getBoundingClientRect().width
        setContainerWidth(width)
      }
    }

    updateWidth()
    window.addEventListener("resize", updateWidth)

    return () => {
      window.removeEventListener("resize", updateWidth)
    }
  }, [])

  // Update thumb position when scroll position changes
  useEffect(() => {
    if (scrollTrackRef.current && scrollThumbRef.current) {
      const trackRect = scrollTrackRef.current.getBoundingClientRect()
      const thumbRect = scrollThumbRef.current.getBoundingClientRect()
      const trackWidth = trackRect.width
      const thumbWidth = thumbRect.width
      const maxLeft = trackWidth - thumbWidth

      if (scrollPosition === 1) {
        scrollThumbRef.current.style.left = `${maxLeft}px`
      } else {
        scrollThumbRef.current.style.left = "0px"
      }
    }
  }, [scrollPosition])

  // Generate calendar cells to fill the entire container width
  const renderCalendarCells = () => {
    // Determine the month range based on scroll position
    const startMonth = scrollPosition === 0 ? 0 : 6
    const endMonth = scrollPosition === 0 ? 6 : 12

    // Calculate the number of cells needed to fill the width
    const cellSize = 3 // 3px per cell
    const cellGap = 1 // 1px gap between cells
    const totalCellWidth = cellSize + cellGap
    const cellsPerRow = Math.floor((containerWidth - 20) / totalCellWidth) // Subtract some padding

    // Create a grid with 7 rows (days of week)
    const grid = []
    for (let row = 0; row < 7; row++) {
      const rowCells = []

      // Fill each row with cells
      for (let col = 0; col < cellsPerRow; col++) {
        // Calculate the date for this cell
        const dayOfYear = col * 7 + row
        const date = new Date(currentYear, 0, 1)
        date.setDate(date.getDate() + dayOfYear)

        // Check if the date is in the current year and within the visible month range
        if (date.getFullYear() === currentYear && date.getMonth() >= startMonth && date.getMonth() < endMonth) {
          const dateString = formatDateString(currentYear, date.getMonth(), date.getDate())
          const count = contributionMap[dateString] || 0
          const level = getContributionLevel(count)
          const colorClass = getColorClass(level)
          const cellKey = `${currentYear}-${date.getMonth()}-${date.getDate()}`

          rowCells.push(
            <Tooltip key={`cell-${row}-${col}`} open={activeCell === cellKey && count > 0}>
              <TooltipTrigger asChild>
                <div
                  className={cn("w-3 h-3 rounded-sm mx-0.5", colorClass)}
                  onMouseEnter={() => handleCellMouseEnter(currentYear, date.getMonth(), date.getDate(), count)}
                  onMouseLeave={() => {
                    setTooltipContent(null)
                    setActiveCell(null)
                  }}
                />
              </TooltipTrigger>
              {count > 0 && (
                <TooltipContent side="top" className="bg-gray-700 border-gray-600 text-white">
                  {tooltipContent}
                </TooltipContent>
              )}
            </Tooltip>,
          )
        } else {
          // Add empty cell to maintain grid structure
          rowCells.push(<div key={`empty-${row}-${col}`} className="w-3 h-3 bg-gray-800 rounded-sm mx-0.5"></div>)
        }
      }

      grid.push(
        <div key={`row-${row}`} className="flex w-full my-0.5">
          {rowCells}
        </div>,
      )
    }

    return grid
  }

  return (
    <div className="w-full max-w-4xl bg-gray-950 text-gray-300 rounded-lg p-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-white">
          {total} contributions in {currentYear}
        </h2>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 text-gray-400 hover:text-white">
              Contribution settings <ChevronDown className="ml-1 h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="bg-gray-900 border-gray-800">
            <DropdownMenuItem className="text-gray-300 hover:bg-gray-800 focus:bg-gray-800">
              Private contributions
            </DropdownMenuItem>
            <DropdownMenuItem className="text-gray-300 hover:bg-gray-800 focus:bg-gray-800">
              Activity overview
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <div className="border border-gray-800 rounded-lg p-4">
        {/* Month labels */}
        <div className="grid grid-cols-[auto_1fr] gap-2" ref={containerRef}>
          <div className="w-8"></div> {/* Empty space for alignment */}
          <div className="flex justify-between w-full">
            {visibleMonths.map((month, index) => (
              <div key={index} className="text-center text-sm">
                {month}
              </div>
            ))}
          </div>
          {/* Calendar grid with weekday labels */}
          <div className="flex flex-col justify-between h-28">
            {visibleWeekdays.map((weekday, index) => (
              <div key={index} className="text-xs">
                {weekday}
              </div>
            ))}
          </div>
          {/* Contribution cells - now filling the entire width */}
          <div className="relative w-full">
            <TooltipProvider>
              <div className="grid grid-rows-7 gap-1 h-28 w-full">{containerWidth > 0 && renderCalendarCells()}</div>
            </TooltipProvider>
          </div>
        </div>

        {/* Custom scrollbar */}
        <div className="mt-4 relative">
          <div
            ref={scrollTrackRef}
            className="h-1 bg-gray-700 rounded-full w-full cursor-pointer"
            onClick={handleTrackClick}
          >
            <div
              ref={scrollThumbRef}
              className="absolute h-3 w-16 bg-gray-500 rounded-full -top-1 cursor-grab active:cursor-grabbing"
              onMouseDown={handleMouseDown}
            ></div>
          </div>
        </div>

        {/* Year pagination controls */}
        <div className="flex items-center justify-center mt-6">
          <YearSelector currentYear={currentYear} onPreviousYear={goToPreviousYear} onNextYear={goToNextYear} />
        </div>

        {/* Legend */}
        <div className="flex items-center justify-between mt-4">
          <a href="#" className="text-sm text-gray-400 hover:text-gray-300">
            Learn how we count contributions
          </a>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400">Less</span>
            <div className="w-3 h-3 rounded-sm bg-gray-800"></div>
            <div className="w-3 h-3 rounded-sm bg-green-900"></div>
            <div className="w-3 h-3 rounded-sm bg-green-700"></div>
            <div className="w-3 h-3 rounded-sm bg-green-500"></div>
            <div className="w-3 h-3 rounded-sm bg-green-300"></div>
            <span className="text-sm text-gray-400">More</span>
          </div>
        </div>
      </div>
    </div>
  )
}
